<template>
	<div class="rootdiv-task">
		<div class="table-div">
			<el-table stripe :data="showTableData" class="table-box" height="100%">
				<el-table-column prop="name" :label="$t('task.table_head_name')" class="table-column"> </el-table-column>
				<el-table-column prop="datasets" :label="$t('task.table_head_dataset')" class="table-column">
					<template slot-scope="scope">
						<el-select v-model="scope.row.datasets" :placeholder="$t('task.please_select')" @change="updateTable">
							<el-option v-for="item in datasetList" :key="item.fileName" :label="item.fileName" :value="item.fileName"> </el-option>
						</el-select>
					</template>
				</el-table-column>
				<el-table-column prop="template" :label="$t('task.table_head_template')" class="table-column">
					<template slot-scope="scope">
						<el-select v-model="scope.row.template" :placeholder="$t('task.please_select')" @change="updateTable">
							<el-option v-for="item in templateList" :key="item.name" :label="item.name" :value="item.name"> </el-option>
						</el-select>
					</template>
				</el-table-column>
				<el-table-column prop="createTime" :label="$t('task.table_head_createtime')" class="table-column"> </el-table-column>
				<el-table-column prop="taskFlag" :label="$t('task.table_head_flag')" class="table-column">
					<template slot-scope="scope">
						<el-tag v-if="scope.row.taskFlag === 'no_running'" type="warning">{{ $t('task.flag_no_running') }}</el-tag>
						<el-tag v-else-if="scope.row.taskFlag === 'running'" type="">{{ $t('task.flag_running') }}</el-tag>
						<el-tag v-else-if="scope.row.taskFlag === 'finished'" type="success">{{ $t('task.flag_finished') }}</el-tag>
						<el-tag v-else-if="scope.row.taskFlag === 'failed'" type="danger">{{ $t('task.flag_failed') }}</el-tag>
					</template>
				</el-table-column>

				<el-table-column class="table-column" width="335"> 
					<template slot="header" slot-scope="scope">
						<el-button @click="pre_createTask" type="primary">{{ $t('task.table_head_createtask') }}</el-button>
						<el-button @click="pre_managementDataSet" type="primary">{{ $t('task.table_head_manadataset') }}</el-button>
					</template>

					<template slot-scope="scope">
						<el-tooltip class="item" effect="dark" :content="$t('task.tip_run_task')" placement="top">
							<el-button @click.native.prevent="pre_runRow(scope.$index, tableData)" type="text" size="small" :disabled="scope.row.taskFlag == 'running'">
								<span class="el-icon-caret-right" style="color: darkcyan; font-size: 1.2rem"></span>
							</el-button>
						</el-tooltip>

						<el-tooltip class="item" effect="dark" :content="$t('task.tip_see_result')" placement="top">
							<el-button @click.native.prevent="checkRow(scope.$index, tableData)" type="text" size="small" :disabled="scope.row.taskFlag == 'running'">
								<span class="el-icon-s-order" style="color: darkorange; font-size: 1.2rem"></span>
							</el-button>
						</el-tooltip>

						<el-tooltip class="item" effect="dark" :content="$t('task.tip_del_task')" placement="top">
							<el-button @click.native.prevent="pre_deleteRow(scope.$index, tableData)" type="text" size="small" :disabled="scope.row.taskFlag == 'running'">
								<span class="el-icon-delete-solid" style="color: darkred; font-size: 1.2rem"></span>
							</el-button>
						</el-tooltip>
					</template>
				</el-table-column>
			</el-table>
		</div>

		<div class="page-div">
			<el-pagination @current-change="handleCurrentChange" :current-page="currentPage" :page-size="pagesize" layout="total, prev, pager, next, jumper" :total="total"> </el-pagination>
		</div>

		<!-- dialoag -->

		<!-- 是否删除任务 -->
		<el-dialog :title="$t('task.do_del_task')" :visible.sync="del_dialog_show" width="30%">
			<span slot="footer" class="dialog-footer">
				<el-button @click="del_dialog_show = false">{{ $t('button.return') }}</el-button>
				<el-button type="primary" @click="deleteRow">{{ $t('button.ok') }}</el-button>
			</span>
		</el-dialog>

		<!-- 是否运行任务 -->
		<el-dialog :title="$t('task.do_run_task')" :visible.sync="run_dialog_show" width="30%">
			<span>{{ $t('task.do_run_task_tip') }}</span>
			<span slot="footer" class="dialog-footer">
				<el-button @click="run_dialog_show = false">{{ $t('button.return') }}</el-button>
				<el-button type="primary" @click="runRow">{{ $t('button.ok') }}</el-button>
			</span>
		</el-dialog>

		<!-- 查看结果 -->
		<el-dialog :title="$t('task.title_task_result')" :visible.sync="check_run_dialog_show" width="60%" v-model="check_run_obj">
			<textarea v-text="check_run_obj['result']" style="width: 100%" rows="30"></textarea>
		</el-dialog>

		<!-- 创建任务 -->
		<el-dialog :title="$t('task.title_create_task')" :visible.sync="create_task_dialog_show" width="30%">
			<el-form ref="form" label-width="auto">
				<el-form-item :label="$t('task.please_input_taskname')" required>
					<el-input :placeholder="$t('task.please_input_taskname')" v-model="create_task_input" clearable> </el-input>
				</el-form-item>
			</el-form>

			<span slot="footer" class="dialog-footer">
				<el-button @click="create_task_dialog_show = false">{{$t('button.return')}}</el-button>
				<el-button type="primary" @click="createTask">{{ $t('button.ok') }}</el-button>
			</span>
		</el-dialog>

		<!-- 管理数据集 -->
		<el-dialog :title="$t('task.title_mana_dataset')" :visible.sync="managementDataset_dialog_show" width="60%" :before-close="handleClose" :append-to-body="true">
			<el-button type="primary" @click="dataset_upload_dialog_show = true;" style="margin-left: 20px; margin-bottom: 10px">{{ $t('task.title_upload_dataset') }}</el-button>

			<el-table :data="datasetList" style="width: 100%" height="400">
				<el-table-column prop="fileName" :label="$t('task.label_filename')"> </el-table-column>
				<el-table-column prop="uploadTime" :label="$t('task.label_uploadtime')"> </el-table-column>
				<el-table-column fixed="right" :label="$t('task.label_order')">
					<template slot-scope="scope">
						<!-- <el-button @click.native.prevent="dataset_checkRow(scope.$index, datasetList)" type="text" size="small" > {{ $t('task.label_check') }} </el-button> -->
						<el-button @click.native.prevent="dataset_deleteRow(scope.$index, datasetList)" type="text" size="small" style="color: darkred;"> {{ $t('task.label_del') }} </el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-dialog>

		<!-- 数据集上传 -->
		<el-dialog :title="$t('task.title_upload')" :visible.sync="dataset_upload_dialog_show" width="400px" >
			<el-upload ref="upload" class="upload-demo" drag :action="uploadActionUrl" multiple :data="extraData" :auto-upload="false" :on-success="uploadSuccess">
				<i class="el-icon-upload"></i>
				<div class="el-upload__text" v-html="$t('task.upload_text')"></div>
                <div class="el-upload__tip" slot="tip">
                     <el-button style="margin-left: 10px;" size="small" type="success" @click="do_uploadDataset">{{ $t('task.upload_button_text') }}</el-button>
                </div>
			</el-upload>
		</el-dialog>
	</div>
</template>

<!-- ------------------------------------------------脚本区域--------------------------------------- -->
<script>
import { axios_instance, baseURL } from "@/axios/index";
export default {
	name: "task",
	data() {
		return {
			// 定时器
			intervalId: null, // 用于存储 setInterval 的 ID，以便后续清除
			// 分页
			currentPage: 1,
			pagesize: 10,
			total: 0,
			showTableData: [],
			tableData_chunkArray: [],
			tableData: [],
			// 删除任务
			del_index: "",
			del_rows: [],
			del_dialog_show: false,
			// 运行任务
			run_index: "",
			run_rows: [],
			run_dialog_show: false,
			templateList: [],
			datasetList: [],

			// 查看运行任务
			check_run_obj: {},
			check_run_dialog_show: false,
			// 创建任务
			create_task_dialog_show: false,
			create_task_input: "",
			// 管理数据集
            managementDataset_dialog_show: false,
            // 上传数据集
            dataset_upload_dialog_show:false,
            extraData : {},
            uploadActionUrl:baseURL + '/uploadDataset'
		};
	},
	watch: {},
	created() {},
	beforeRouteLeave(to, from, next) {
		if (this.intervalId) {
			clearInterval(this.intervalId);
			this.intervalId = null;
		}
		next();
	},

	mounted() {
		// 初始化 模板
        this.getTemplateData();
		// 初始化 数据集
        this.getDatasetData();

		this.getTableData(); // 立即请求一次
		this.intervalId = setInterval(this.getTableData, 3000);
	},
	methods: {
		handleClose(done) {
			this.$confirm(this.$t('task.code_close'))
				.then((_) => {
					done();
				})
				.catch((_) => {});
		},

		// 获取格式化时间
		getformatDateToStr() {
			const date = new Date();
			const day = String(date.getDate()).padStart(2, "0");
			const month = String(date.getMonth() + 1).padStart(2, "0"); // 月份从0开始，所以要加1
			const year = date.getFullYear();
			const hours = String(date.getHours()).padStart(2, "0");
			const minutes = String(date.getMinutes()).padStart(2, "0");
			const seconds = String(date.getSeconds()).padStart(2, "0");
			return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
		},

		getTableData() {
			axios_instance
				.get("/getTaskDataList")
				.then((res) => {
					this.tableData = res.data.data;
					this.total = this.tableData.length;
					this.tableData_chunkArray = this.chunkArray(this.tableData, this.pagesize);
					this.handleCurrentChange(this.currentPage);
				})
				.catch((err) => {});
        },
        getDatasetData() {
            axios_instance
                .get("/getDataSetList")
                .then((res) => {
                    this.datasetList = res.data.data;
                })
                .catch((err) => {
                    console.log(err);
                });
        },

        getTemplateData() {
            axios_instance
                .get("/getInitConfig")
                .then((res) => {
                    this.templateList = res.data.data;
                })
                .catch((err) => {
                    console.log(err);
                });
        },

		// 每当tableData改变的时候，重新计算
		updateTable() {
			// 同步当前table数据到后台
			let param = {
				data: this.tableData,
			};
			axios_instance
				.post("/updateTaskData", param)
				.then((res) => {
					this.tableData = res.data.data;
				})
				.catch((err) => {});
			this.total = this.tableData.length;
			this.tableData_chunkArray = this.chunkArray(this.tableData, this.pagesize);
			this.handleCurrentChange(this.currentPage);
		},

		// 同步数据集数据到后台
		updateDataset() {
			let param = {
				data: this.datasetList,
			};
			axios_instance
				.post("/updateDataSetList", param)
				.then((res) => {
					this.tableData = res.data.data;
				})
				.catch((err) => {});
		},

		// 翻页
		handleCurrentChange(val) {
			// console.log(`当前页: ${val - 1}`);
			this.currentPage = val;
			this.showTableData = this.tableData_chunkArray[val - 1];
			// console.log(this.showTableData);
			if (this.showTableData == undefined || this.showTableData == "undefined" || this.showTableData.length == 0) {
				this.currentPage = this.currentPage - 1;
				this.showTableData = this.tableData_chunkArray[this.currentPage - 1];
			}
		},

		// 按固定长度分割数组
		chunkArray(array, chunkSize) {
			if (chunkSize <= 0) {
				throw new Error("chunkSize must be greater than 0");
			}

			const result = [];
			for (let i = 0; i < array.length; i += chunkSize) {
				const chunk = array.slice(i, i + chunkSize);
				result.push(chunk);
			}
			return result;
		},

		// 管理数据集
		pre_managementDataSet() {
			console.log("uploadDataSet");
			this.managementDataset_dialog_show = true;
		},


		// 上传数据集
		do_uploadDataset() {
            this.extraData["uploadTime"] = this.getformatDateToStr();
            // 上传到服务器
            this.$refs.upload.submit();
		},
        uploadSuccess(response, file, fileList) {
            this.$message({
                message: this.$t('task.code_upload_ok'),
                type: "success",
                duration: 1500,
            });
            this.getDatasetData();
        },


		//查看数据集(查看前10条)
		dataset_checkRow(index, tableData) {
			console.log("🚀 -> index:\n", index);
		},

		//删除数据集
		dataset_deleteRow(index, tableData) {
			console.log("🚀 -> index:\n", index);
			tableData.splice(index, 1);
			this.updateDataset();
			this.$message({
				message: this.$t('task.code_del_ok'),
				type: "success",
				duration: 1500,
			});
		},

		// 创建任务
		pre_createTask() {
			this.create_task_dialog_show = true;
		},
		createTask() {
			console.log(this.create_task_input);

			if (this.create_task_input == "") {
				this.$message({
					message: this.$t('task.code_pleate_input_taskname'),
					type: "warning",
				});
				return;
			}

			for (let i in this.tableData) {
				if (this.tableData[i].name == this.create_task_input) {
					this.$message({
						message: this.$t('task.code_taskname_not_repeat'),
						type: "warning",
					});
					return;
				}
			}

			let obj = {
				createTime: this.getformatDateToStr(),
				datasets: "",
				name: this.create_task_input,
				taskFlag: "no_running",
				template: "",
				result: "",
			};
			console.log("🚀 -> obj:\n", obj);

			this.tableData.push(obj);
			this.updateTable();

			this.create_task_dialog_show = false;
			this.$message({
				message: this.$t('task.code_add_ok'),
				type: "success",
				duration: 1500,
			});
		},

		// no_running
		// running
		// finished
		// failed
		// 运行任务
		pre_runRow(index, rows) {
			this.run_rows = rows;
			this.run_index = index;

			let check_index = this.pagesize * (this.currentPage - 1) + this.run_index;
			if (this.run_rows[check_index]["datasets"] == "") {
				this.$message({
					message: this.$t('task.code_please_select_dataset'),
					type: "warning",
					duration: 1500,
				});
				return;
			}
			if (this.run_rows[check_index]["template"] == "") {
				this.$message({
					message: this.$t('task.code_please_select_template'),
					type: "warning",
					duration: 1500,
				});
				return;
			}
			this.run_dialog_show = true;
		},
		runRow() {
			let index = this.pagesize * (this.currentPage - 1) + this.run_index;
			// console.log("运行任务", this.del_rows[index]);
			// 运行任务
			let param = {
				run_data: this.run_rows[index],
			};
			axios_instance
                .post("/runTaskData", param, { timeout: 0 })
				.then((res) => {
					console.log(res);
				})
				.catch((err) => {});

			this.run_dialog_show = false;
			this.$message({
				message: this.$t('task.code_run_task'),
				type: "success",
				duration: 1500,
			});
		},

		// 检查任务
		checkRow(index, rows) {
			index = this.pagesize * (this.currentPage - 1) + index;
			this.check_run_obj = JSON.parse(JSON.stringify(rows[index]));
			this.check_run_dialog_show = true;
		},

		// 删除任务
		pre_deleteRow(index, rows) {
			this.del_rows = rows;
			this.del_index = index;
			this.del_dialog_show = true;
		},
		deleteRow() {
			let index = this.pagesize * (this.currentPage - 1) + this.del_index;
			this.del_rows.splice(index, 1);
			this.updateTable();
			this.del_dialog_show = false;
			this.$message({
				message: this.$t('task.code_del_ok'),
				type: "success",
				duration: 1500,
			});
		},
	},
};
</script>


<style scoped>
.el-table >>> th {
	text-align: center !important;
}
.el-table >>> td {
	text-align: center !important;
}


.rootdiv-task {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	height: calc(100vh - 100px);
}

.table-div {
	width: 100%;
	/* height: calc(100% - 55px); */
	height: calc(100% - 104px);
}

.table-box {
	/* margin-left: 30px; */
	/* margin-right: 30px; */
	/* margin-top: 5px; */
	width: calc(100%);
	/* height:708px; */
	/* max-height:calc(100% - 0px); */
	display: flex;
	flex-direction: column;
}
.table-column {
	/* text-align: center; */
}

.page-div {
	margin-top: 50px;
	margin-right: 40px;
}
</style>
