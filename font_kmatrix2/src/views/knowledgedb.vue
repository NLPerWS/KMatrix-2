<template>
	<div class="rootdiv">
		<div class="titlediv">
			<div class="showTextDiv">
				<p>{{ $t("knowledge.title1") }}</p>
				<p>{{ $t("knowledge.title2") }}</p>
			</div>
			<div class="creatediv">
				<el-input class="searchInput" :placeholder="$t('knowledge.searchdb')" v-model="searchDbInput" clearable @input="do_filter_db"> </el-input>

				<el-button class="createButton" type="primary" size="medium" icon="el-icon-edit" @click="pre_createDB">{{ $t("knowledge.createdb") }}</el-button>
				
			</div>
		</div>

		<div class="maindiv" v-if="show_dbInfoList.length > 0">
			<div class="dbItem" v-for="item in show_dbInfoList">
				<div style="width: 75%; padding: 20px">
					<div style="font-size: 1.65rem; font-weight: 400; height: 95px; overflow-wrap: break-word; white-space: normal; overflow-y: hidden; color: darkcyan">{{ item.infoName }}</div>
					<div style="margin-top: 40px; font-size: 0.9rem"><span class="el-icon-s-cooperation"></span> <strong>Type is:</strong> &nbsp;{{ item.infoType.join(" -> ") }}</div>
					<div style="margin-top: 20px; font-size: 0.9rem"><span class="el-icon-s-claim"></span> <strong>Create at:</strong> &nbsp;{{ item.createTime }}</div>
				</div>
				<div style="display: flex; flex-direction: column">

					<el-tooltip :content="$t('knowledge.uploadfile')" placement="right">
						<span class="el-icon-upload icon-size" style="color: steelblue" v-if="item.infoUploadType != '' || item['infoType'][1] == 'MysqlDB'  || item['infoType'][1] == 'GraphDB'  || item['infoType'][1] == 'Neo4jDB'" @click="pre_upload(item)"></span>
					</el-tooltip>

					<el-tooltip :content="$t('knowledge.checkfile')" placement="right">
						<span class="el-icon-s-order icon-size" style="color: teal" v-if="item.infoUploadType != '' || item['infoType'][1] == 'MysqlDB'  || item['infoType'][1] == 'GraphDB'  || item['infoType'][1] == 'Neo4jDB'" @click="pre_check_upload_file(item)"></span>
					</el-tooltip>

					<el-tooltip :content="$t('knowledge.updateconfig')" placement="right">
						<span class="el-icon-s-tools icon-size" style="color: saddlebrown" @click="pre_updateDB(item)"></span>
					</el-tooltip>

					<el-tooltip :content="$t('knowledge.deldb')" placement="right">
						<span class="el-icon-delete-solid icon-size" style="color: brown" @click="pre_deleteDB(item)"></span>
					</el-tooltip>
				</div>
			</div>
		</div>

		<div v-else class="nodbdiv">
			<el-empty :description="$t('knowledge.emptydb')"></el-empty>
		</div>

		<!-- dialig -->
		<!-- createdb -->

		<el-dialog :title="$t('knowledge.title_db')" :visible.sync="dialogVisible_create_update" width="550px" :before-close="handleClose" :append-to-body="true">
			<el-form ref="form" :model="updateDbObj" label-width="100px">
				<el-form-item :label="$t('knowledge.title_name')" required>
					<el-input v-model="updateDbObj.infoName" style="width: 217px"></el-input>
				</el-form-item>

				<el-form-item :label="$t('knowledge.title_type')" required>
					<!-- <el-cascader-panel :disabled="cascader_disable" :options="dbTypeList" @change="changeSelectType" v-model="updateDbObj.infoType"></el-cascader-panel> -->

					<el-cascader :disabled="cascader_disable" :options="dbTypeList" @change="changeSelectType" v-model="updateDbObj.infoType"></el-cascader>
				</el-form-item>

				<el-divider content-position="left"></el-divider>

				<el-form-item label-width="130px" v-if="updateDbObj.infoType.length > 1 && updateDbObj.infoType[1].includes('DB')" required :label="$t('knowledge.from_link')">
					<el-input v-model="updateDbObj.dbHost"></el-input>
				</el-form-item>
				<el-form-item label-width="130px" v-if="updateDbObj.infoType.length > 1 && updateDbObj.infoType[1].includes('DB')" required :label="$t('knowledge.from_name')">
					<el-input v-model="updateDbObj.dbName"></el-input>
				</el-form-item>
				<el-form-item label-width="130px" v-if="updateDbObj.infoType.length > 1 && updateDbObj.infoType[1].includes('DB')" required :label="$t('knowledge.from_username')">
					<el-input v-model="updateDbObj.dbUsername"></el-input>
				</el-form-item>
				<el-form-item label-width="130px" v-if="updateDbObj.infoType.length > 1 && updateDbObj.infoType[1].includes('DB')" required :label="$t('knowledge.from_password')">
					<el-input v-model="updateDbObj.dbPassword"></el-input>
				</el-form-item>

				<!-- <el-form-item v-if="updateDbObj.infoType.length > 1 && (updateDbObj.infoType[1].includes('MysqlDB') || updateDbObj.infoType[1].includes('GraphDB') || updateDbObj.infoType[1].includes('Neo4jDB'))" :label="$t('knowledge.from_upload')">
					<el-tag>{{ $t("knowledge.from_no_config") }}</el-tag>
				</el-form-item> -->

				<el-form-item v-else-if="updateDbObj.infoType.length > 1 && !updateDbObj.infoType[1].includes('DB')" :label="$t('knowledge.from_upload')">
					<el-tag>{{ $t("knowledge.from_no_config") }}</el-tag>
				</el-form-item>

				<el-form-item v-else>
					<el-empty :description="$t('knowledge.from_no_knowledge')" style="margin-right: 70px"></el-empty>
				</el-form-item>
			</el-form>

			<span slot="footer" class="dialog-footer">
				<el-button @click="dialogVisible_create_update = false">{{ $t("button.return") }}</el-button>
				<el-button type="primary" @click="execute_click">{{ $t("button.ok") }}</el-button>
			</span>
		</el-dialog>

		<!-- 删除知识库 -->
		<el-dialog :visible.sync="dialogVisible_delete_tip" width="30%" :append-to-body="true">
			<span style="font-size: 1.05rem; font-weight: 540">{{ $t("knowledge.title_deldb") }}</span>
			<span slot="footer" class="dialog-footer">
				<el-button @click="dialogVisible_delete_tip = false">{{ $t("button.return") }}</el-button>
				<el-button type="primary" @click="execute_click">{{ $t("button.ok") }}</el-button>
			</span>
		</el-dialog>

		<!-- 上传文件 -->
		<el-dialog :title="$t('knowledge.title_upload')" :visible.sync="dialogTableVisible_upload" width="280px" :append-to-body="true" v-model="updateDbObj">
			<el-upload multiple :data="extraData" class="upload-demo" ref="upload" :file-list="fileList" :accept="updateDbObj.infoUploadType" :show-file-list="true" :auto-upload="false" :action="uploadUrl" :on-success="upload_success">
				<el-button style="margin-left: 10px" slot="trigger" size="small" type="primary">{{ $t("knowledge.title_upload_step1") }}</el-button>
				<el-button style="margin-left: 10px; margin-top: 20px" size="small" type="success" @click="submitUpload">{{ $t("knowledge.title_upload_step2") }}</el-button>
			</el-upload>
		</el-dialog>

		<!-- 查看知识库文件数据 -->
		<el-dialog :title="$t('knowledge.title_check_file')" :visible.sync="dialogTableVisible_check" width="60%" :append-to-body="true" :before-close="handleClose">
			<!-- <span>{{ show_knowlede_data_list }}</span> -->
			<el-table :data="show_knowlede_data_list" style="width: 100%" height="600" stripe>
				<el-table-column type="expand">
					<template slot-scope="props">

                        <div v-for="(item, index) in props.row.children" :key="index" style="white-space: pre; overflow-x: auto;" v-text="JSON.stringify(item,null,4)">
						</div>

					</template>
				</el-table-column>
				<el-table-column :label="$t('knowledge.check_file_label_fileName')" prop="value"> </el-table-column>
                <el-table-column
                :label="$t('knowledge.check_file_label_fileName')"
                width="120">
                <template slot-scope="scope">
                    <el-button
                    @click.native.prevent="deleteRow_knowledge(scope.$index, show_knowlede_data_list)"
                    type="text"
                    size="small">
                    {{ $t('knowledge.check_file_label_del') }}
                    </el-button>
                </template>
                </el-table-column>
			</el-table>
		</el-dialog>
	</div>
</template>

<script>
import { axios_instance, baseURL } from "@/axios/index";

var defaultObj = {
	dbHost: "",
	dbName: "",
	dbPassword: "",
	dbUsername: "",
	infoName: "",
	infoType: "",
	infoUploadType: "",
	createTime: "",
};

export default {
	data() {
		return {
			// 展示
			dbInfoList: [],
			show_dbInfoList: [],
			searchDbInput: "",
			// 更新 添加
			updateDbObj: defaultObj,
			origin_updateDb_name: "",
			cascader_disable: false,
			// 创建知识库用
			dialogVisible_create_update: false,
			dbTypeList: [],
			selectDbType: [],
			order_type: "",
			// 删除知识库
			dialogVisible_delete_tip: false,
			// 上传文件
			dialogTableVisible_upload: false,
			fileList: [],
			extraData: {},
			uploadUrl: baseURL + "/uploadKnowledge",
			// 查看文件
			dialogTableVisible_check: false,
            show_knowlede_data_list: [],
            thisClickRowValue:{},
		};
	},

	mounted() {
		axios_instance
			.get("/getDataBaseType")
			.then((res) => {
				this.dbTypeList = res.data.data;
				console.log("🚀 -> this.dbTypeList:\n", this.dbTypeList);
			})
			.catch((err) => {});
		this.getDbData();
	},

	methods: {
		handleClose(done) {
			this.$confirm(this.$t("knowledge.code_close"))
				.then((_) => {
					done();
				})
				.catch((_) => {});
		},

		// 获取格式化时间
		getformatDateToStr() {
			const date = new Date();
			const day = String(date.getDate()).padStart(2, "0");
			const month = String(date.getMonth() + 1).padStart(2, "0"); 
			const year = date.getFullYear();
			const hours = String(date.getHours()).padStart(2, "0");
			const minutes = String(date.getMinutes()).padStart(2, "0");
			const seconds = String(date.getSeconds()).padStart(2, "0");
			return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
		},

		// 搜索知识库
		do_filter_db() {
			if (this.searchDbInput == "") {
				this.show_dbInfoList = [].concat(this.dbInfoList);
			} else {
				this.show_dbInfoList = [].concat(this.dbInfoList.filter((item) => item.infoName.indexOf(this.searchDbInput) > -1));
			}
		},

		// 获取最新的数据库数据
		getDbData() {
			axios_instance
				.get("/getDataBaseData")
				.then((res) => {
					this.dbInfoList = res.data.data;
					this.show_dbInfoList = res.data.data;
				})
				.catch((err) => {});
		},

		// 更新知识库数据
        updateDbData(order, useDb, origin_Db_name) {
            
            useDb['infoPath'] = useDb['infoName'].replaceAll("/", "_");

			let param = {
				order: order,
				data: useDb,
				origin_Db_name: origin_Db_name,
            };

			axios_instance
				.post("/updateDbConfig", param)
				.then((res) => {
					this.dbInfoList = res.data.data;
					this.show_dbInfoList = res.data.data;
				})
				.catch((err) => {});
		},


		changeSelectType(value) {
			this.selectDbType = value;
			for (let i in this.dbTypeList) {
				if (this.dbTypeList[i]["value"] == this.selectDbType[0]) {
					for (let j in this.dbTypeList[i]["children"]) {
						if (this.dbTypeList[i]["children"][j]["value"] == this.selectDbType[1]) {
							this.updateDbObj.infoUploadType = this.dbTypeList[i]["children"][j]["acceptType"];
						}
					}
				}
			}
			console.log(this.updateDbObj);
		},

		pre_createDB() {
			this.cascader_disable = false;
			this.dialogVisible_create_update = true;
			this.updateDbObj = JSON.parse(JSON.stringify(defaultObj));
			this.order_type = "add";
		},
		pre_upload(value) {
			this.dialogTableVisible_upload = true;
			this.updateDbObj = JSON.parse(JSON.stringify(value));
			this.order_type = "upload";
		},
		pre_check_upload_file(value) {
            // console.log("🚀 -> value:\n", value)
            this.thisClickRowValue = value;
			let msg = this.$message({
				message: this.$t("knowledge.getSampleData"),
				type: "warning",
				duration: 0,
			});

			let param = {
                infoName: value["infoName"],
                infoType: value["infoType"],
			};
			// 获取知识数据
			axios_instance
				.post("/getDataBaseKnowledgeData", param ,{ timeout: 0 })
				.then((res) => {
                    this.show_knowlede_data_list = res.data.data;
                    msg.close();
					this.order_type = "check";
                    this.dialogTableVisible_check = true;
				})
				.catch((err) => {});

			// this.updateDbObj = JSON.parse(JSON.stringify(value));
			// this.order_type = "check";
			// this.dialogTableVisible_check = true;
		},

        // 删除一个数据文件
        deleteRow_knowledge(index, dataList) {
            // console.log("🚀 -> index:\n", index)
            // console.log("🚀 -> this.thisClickRowValue:\n", this.thisClickRowValue)
            // console.log("🚀 -> dataList:\n", dataList)

			let param = {
                infoName: this.thisClickRowValue["infoName"],
                infoType: this.thisClickRowValue["infoType"],
                delFileName: dataList[index]["value"],
			};

			axios_instance
				.post("/delDataBaseKnoeledgeData", param,{ timeout: 0 })
				.then((res) => {
                    this.show_knowlede_data_list = res.data.data;
					this.order_type = "check";
                    this.dialogTableVisible_check = true;
                    this.$message({
                        message: this.$t("knowledge.del_ok"),
                        type: "success",
                        duration: 1000,
                    });

				})
				.catch((err) => {});
                
        },

		pre_updateDB(value) {
			this.cascader_disable = true;
			this.dialogVisible_create_update = true;
			this.updateDbObj = JSON.parse(JSON.stringify(value));
			this.origin_updateDb_name = this.updateDbObj.infoName;
			this.order_type = "update";
		},
		pre_deleteDB(value) {
			this.dialogVisible_delete_tip = true;
			this.updateDbObj = JSON.parse(JSON.stringify(value));
			this.order_type = "delete";
		},

		execute_click() {
			if (this.order_type == "add") {
				this.createDB();
			} else if (this.order_type == "update") {
				this.updateDB();
			} else if (this.order_type == "delete") {
				this.deleteDb();
			} else {
				this.$message({
					message: this.$t("knowledge.ordererr"),
                    type: "warning",
                    duration: 1000,
				});
				return;
			}
		},
		submitUpload() {
			this.extraData["savePath"] = this.updateDbObj.infoName;
			this.$refs.upload.submit();
		},
		upload_success() {
			this.$message({
				message: this.$t("knowledge.uploadok"),
                type: "success",
                duration: 1000,
			});
			this.fileList = [];
		},

		// 创建知识库
		createDB() {
			this.updateDbObj.createTime = this.getformatDateToStr();
			console.log("🚀 -> this.updateDbObj:\n", this.updateDbObj);
			if (this.updateDbObj.infoName == "") {
				this.$message({
					message: this.$t("knowledge.please_input_name"),
                    type: "warning",
                    duration: 2000,
				});
				return;
			}
			if (this.updateDbObj.infoType.length == 0) {
				this.$message({
					message: this.$t("knowledge.please_select_type"),
                    type: "warning",
                    duration: 2000,
				});
				return;
			}
			if (this.updateDbObj.infoType[1].includes("DB") && (this.updateDbObj.dbHost == "" || this.updateDbObj.dbName == "" || this.updateDbObj.dbUsername == "" || this.updateDbObj.dbPassword == "")) {
				this.$message({
					message: this.$t("knowledge.please_input_info"),
                    type: "warning",
                    duration: 2000,
				});
				return;
			}

			for (let i in this.dbInfoList) {
				if (this.dbInfoList[i].infoName == this.updateDbObj.infoName) {
					this.$message({
						message: this.$t("knowledge.name_not_repeat"),
                        type: "warning",
                        duration: 2000,
					});
					return;
				}
			}

            if (!this.updateDbObj['infoName'].includes("/")) {
                this.$message({
                    message: this.$t("knowledge.code_error_db_name"),
                    type: "warning",
                    duration: 1000,
                });
                return;
            }

            this.dialogVisible_create_update = false;
			this.updateDbData(this.order_type, this.updateDbObj, this.updateDbObj.infoName);
			this.$message({
				message: this.$t("knowledge.add_ok"),
				type: "success",
                duration: 1000,
			});
		},

		// 更新知识库
		updateDB() {
			for (let i in this.dbInfoList) {
				if (this.dbInfoList[i].infoName == this.updateDbObj.infoName && this.updateDbObj.infoName != this.origin_updateDb_name) {
					this.$message({
						message: this.$t("knowledge.name_not_repeat"),
                        type: "warning",
                        duration: 2000,
					});
					return;
				}
            }

            if (!this.updateDbObj['infoName'].includes("/")) {
                this.$message({
                    message: this.$t("knowledge.code_error_db_name"),
                    type: "warning",
                    duration: 1000,
                });
                return;
            }
            
			this.updateDbData(this.order_type, this.updateDbObj, this.origin_updateDb_name);
			this.dialogVisible_create_update = false;
			this.$message({
				message: this.$t("knowledge.update_ok"),
                type: "success",
                duration: 1000,
			});
		},

		deleteDb() {
			this.updateDbData(this.order_type, this.updateDbObj, this.updateDbObj.infoName);
			this.$message({
				message: this.$t("knowledge.del_ok"),
                type: "success",
                duration: 1000,
			});
			this.dialogVisible_delete_tip = false;
		},

		// 知识融合
		fusionKnowledge() {},
	},
};
</script>

<style scoped>
.rootdiv {
	display: flex;
	flex-direction: column;
	/* width: calc(100% - 100px); */
	height: calc(100vh - 100px);
}
.titlediv {
	/* background-color: antiquewhite; */
	/* width: 100%; */
	height: 120px;
	display: flex;
	flex-direction: row;
	justify-content: space-between;
	align-items: center;
}

.showTextDiv {
	/* background-color: aquamarine; */
	margin-left: 65px;
	width: 800px;
	font-size: 1.5rem;
	font-weight: 1000;
	font-family: "Franklin Gothic Medium", "Arial Narrow", Arial, sans-serif;
}

.creatediv {
	/* background-color: aqua; */
	width: 600px;
	height: 90px;
	display: flex;
	align-items: center;
	margin-right: 65px;
}
.searchInput {
	width: 400px;
}
.createButton {
	margin-left: 20px;
	height: 40px;
}

.maindiv {
	/* background-color: orange; */
	/* width: 100%; */
	height: calc(100% - 120px);
	padding: 50px;
	padding-left: 0px;
	padding-top: 0px;
	padding-right: 0px;
	display: flex;
	flex-direction: row;
	flex-wrap: wrap;
	justify-content: flex-start;
	overflow-y: auto;
    align-content: flex-start;
}
.nodbdiv {
	height: 100%;
	width: 100%;
}

.dbItem {
	height: 250px;
	width: 410px;
	margin-left: 50px;
	margin-top: 50px;
	background-color: white; /* 背景颜色 */
	border-radius: 10px; /* 圆角 */
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1), 0 6px 20px rgba(0, 0, 0, 0.1); /* 阴影效果 */
	transition: transform 0.3s, box-shadow 0.3s; /* 过渡效果 */
	border-top: 0.4px solid #ebebeb; /* 上边框颜色和厚度 */

	display: flex;
}

.dbItem:hover {
	transform: translateY(-10px); /* 悬停时上移 */
	box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2), 0 12px 40px rgba(0, 0, 0, 0.2); /* 悬停时阴影加深 */
}

.icon-size {
	margin-top: 22px;
	font-size: 25px !important;
	width: 35px;
	height: 35px;
	text-align: center;
	line-height: 35px;
	background-color: white; /* 背景颜色 */
	border-radius: 10px; /* 圆角 */
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1), 0 6px 20px rgba(0, 0, 0, 0.1); /* 阴影效果 */
	transform: none !important;
}
.icon-size:hover {
	transform: translateY(-10px); /* 悬停时上移 */
	box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2), 0 12px 40px rgba(0, 0, 0, 0.2); /* 悬停时阴影加深 */
}
</style>
