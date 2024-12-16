<template>
	<div class="chatroot">
		<div class="templatediv">
			<div style="margin-top: 5px">
				<el-button type="primary" style="width: 98%" @click="pre_add_template">{{ $t("chat.title") }}</el-button>
			</div>
			<el-divider></el-divider>

			<div class="template-list">
				<div class="template-list-item" @click="clickTemplateItem(item)" :id="item.name" v-for="item in templateList">
					<div style="width: calc(100% - 30px); margin-right: 10px">
						<div style="font-size: 0.9rem; overflow-x: hidden">
							<strong>{{ item.name }}</strong>
						</div>
						<div style="font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif; font-size: 0.9rem; color: #aeaeaf">{{ item.des }}</div>
					</div>

					<div style="display: flex; flex-direction: column; justify-content: space-between; width: 30px">
						<el-tooltip class="item" effect="dark" :content="$t('tip.deployTip')" placement="right">
							<a class="el-icon-video-play" style="color: #41b883" @click="pre_click_template(item, 'deploy')"></a>
						</el-tooltip>
						<el-tooltip class="item" effect="dark" :content="$t('tip.updateTemplateTip')" placement="right">
							<a class="el-icon-s-operation" style="color: #e6a23c" @click="pre_click_template(item, 'update')"></a>
						</el-tooltip>
						<el-tooltip class="item" effect="dark" :content="$t('tip.deleteTemplateTip')" placement="right">
							<a class="el-icon-delete" style="color: #f56c6c" @click="pre_click_template(item, 'delete')"></a>
						</el-tooltip>
					</div>
				</div>
			</div>
		</div>
		<el-divider direction="vertical" class="template-divider"></el-divider>

		<div class="chatdiv">
			<div class="chat-res">
				<div class="chat-res-dev" ref="scrollableDiv">
					<div v-for="item in chatHisList" :key="item.id">
						<div :class="item.role === 'bot' ? 'chat-res-dev-item-bot-logo' : 'chat-res-dev-item-user-logo'"></div>
						<div :class="item.role === 'bot' ? 'chat-res-dev-item-bot' : 'chat-res-dev-item-user'">
							{{ item.text }}
							<el-tooltip effect="light" v-if="item.ctxs.length > 0">
								<div slot="content" style="font-size: 0.85rem; padding: 10px; width: 500px; height: 500px; overflow-y: auto; word-wrap: break-word; white-space: pre-wrap">{{ item.ctxs.map((item) => item.content).join("\n----------------------------------------------------------------------------------\n") }}</div>
								<!-- <span class="el-icon-s-promotion" ></span> -->
								<span v-if="item.ctxs.length > 0" class="el-icon-s-promotion"></span>
							</el-tooltip>
						</div>
					</div>
				</div>
			</div>

			<div class="chat-input">
				<el-tooltip class="item" effect="dark" :content="$t('tip.deleteChaHisTip')" placement="top">
					<div class="el-icon-delete-solid" @click="clearTemChatHis"></div>
				</el-tooltip>

				<el-select style="width: calc(100% - 300px)" v-model="input" filterable allow-create default-first-option clearable :placeholder="$t('chat.please_input')">
					<el-option v-for="(item, index) in input_list" :key="index" :label="item" :value="item"> </el-option>
				</el-select>

				<el-button style="margin-left: 15px; width: 100px" type="primary" icon="el-icon-s-promotion" :loading="chat_loading" @click="do_chat('chat', '')">&nbsp;&nbsp;{{ $t("chat.do_chat") }}</el-button>
			</div>
		</div>

		<!-- 部署模板模型 dialog -->
		<el-dialog :visible.sync="dis_deploy" width="30%" :append-to-body="true">
			<span>{{ $t("chat.deploy_dialog") }}</span>
			<span slot="footer" class="dialog-footer">
				<el-button @click="dis_deploy = false">{{ $t("button.return") }}</el-button>
				<el-button type="primary" @click="deployTem">{{ $t("button.ok") }}</el-button>
			</span>
		</el-dialog>

		<el-drawer :title="$t('template.createOrUpdate')" :visible.sync="dis_update" direction="rtl" :before-close="handleClose" size="35%" :append-to-body="true">
			<el-form ref="form" v-model="updateTemplateInfo" label-width="170px" style="height: calc(100% - 100px); overflow-y: auto">
				<el-form-item :label="$t('template.name')" required>
					<el-input v-model="updateTemplateInfo.name"></el-input>
				</el-form-item>
				<el-form-item :label="$t('template.type')" required>
					<el-select v-model="updateTemplateInfo.type" :placeholder="$t('template.pleaseSelect')">
						<el-option v-for="item in templateTypeList" :key="item" :label="item" :value="item"></el-option>
					</el-select>
				</el-form-item>

				<el-form-item :label="$t('template.hello')">
					<el-input v-model="updateTemplateInfo.hello" type="textarea" rows="2"></el-input>
				</el-form-item>

				<el-form-item :label="$t('template.des')">
					<el-input v-model="updateTemplateInfo.des" type="textarea" rows="2"></el-input>
				</el-form-item>

				<el-form-item :label="$t('template.prompt')">
					<el-input v-model="updateTemplateInfo.prompt" type="textarea" rows="8"></el-input>
                    <div v-if="updateTemplateInfo.prompt != ''" v-text="$t('template.prompt_des')" style="color: gray; margin-left: 25px"></div>
				</el-form-item>

				<el-form-item :label="$t('template.db')" required>
					<el-tooltip class="item" effect="dark" :content="$t('tip.db')" placement="top">
						<span class="el-icon-question"></span>
					</el-tooltip>
					<!-- <el-select v-model="do_selectDbNameList"  :placeholder="$t('template.pleaseSelect')" style="margin-left: 10px"  @change="changeSelectDbName"> -->
					<el-select v-model="do_selectDbNameList" multiple :placeholder="$t('template.pleaseSelect')" style="margin-left: 10px" @change="changeSelectDbName">
						<el-option v-for="item in dbNameSelectList" :key="item" :label="item" :value="item"> </el-option>
					</el-select>
					<div v-if="do_liner_flag" v-text="$t('template.doliner')" style="color: gray; margin-left: 25px"></div>
					<div v-if="do_interface_flag" v-text="$t('template.dointerface')" style="color: gray; margin-left: 25px"></div>
				</el-form-item>

				<el-divider></el-divider>

				<el-form-item :label="$t('template.retriever')" required>
					<el-tooltip class="item" effect="dark" :content="$t('tip.retriever')" placement="top">
						<span class="el-icon-question"></span>
					</el-tooltip>
					<el-select v-model="updateTemplateInfo.retrieverModelInfo.modelNameList" multiple :placeholder="$t('template.pleaseSelect')" style="margin-left: 10px" @visible-change="getRetrieverList" @change="changeSelectRetriever">
						<el-option v-for="item in retrieverModelSelectList" :key="item.value" :label="item.label" :value="item.value"> </el-option>
					</el-select>
				</el-form-item>

				<el-form-item label="topk">
					<el-tooltip class="item" effect="dark" :content="$t('tip.retriever_topk')" placement="top">
						<span class="el-icon-question"></span>
					</el-tooltip>
					<el-slider v-model="updateTemplateInfo.retrieverModelInfo.topk" :min="retriever_min" :max="retriever_max" style="width: 60%; margin-left: 20px"></el-slider>
				</el-form-item>

				<el-form-item :label="$t('template.check_knowledge_diff_switch')" required>
					<el-tooltip class="item" effect="dark" :content="$t('tip.check_knowledge_diff_switch')" placement="top">
						<span class="el-icon-question"></span>
					</el-tooltip>

                    <el-switch
                        style="display: block; margin-left: 50px"
                        v-model="updateTemplateInfo.knowledgeDiffSwitch"
                        active-color="#13ce66"
                        inactive-color="#ff4949"
                        active-text="open"
                        inactive-text="close">
                    </el-switch>

				</el-form-item>


				<el-form-item :label="$t('template.check_knowledge_diff')" required>
					<el-tooltip class="item" effect="dark" :content="$t('tip.check_knowledge_diff')" placement="top">
						<span class="el-icon-question"></span>
					</el-tooltip>
					<el-select v-model="updateTemplateInfo.knowledgeDiffFunction" :placeholder="$t('template.pleaseSelect')" style="margin-left: 10px" @visible-change="getknowledgeDiffFunction" >
						<el-option v-for="item in knowledgeDiffFunction_list" :key="item.value" :label="item.label" :value="item.value"> </el-option>
					</el-select>
				</el-form-item>

				<el-divider></el-divider>

				<el-form-item :label="$t('template.llm')" required>
					<el-tooltip class="item" effect="dark" :content="$t('tip.llm')" placement="top">
						<span class="el-icon-question"></span>
					</el-tooltip>
					<el-select v-model="updateTemplateInfo.llmModelInfo.modelName" :placeholder="$t('template.pleaseSelect')" style="margin-left: 10px">
						<el-option v-for="item in llmModelSelectList" :key="item" :label="item" :value="item"> </el-option>
					</el-select>
				</el-form-item>

				<el-form-item label="MaxToken">
					<el-tooltip class="item" effect="dark" :content="$t('tip.llm_maxToken')" placement="top">
						<span class="el-icon-question"></span>
					</el-tooltip>
					<el-slider v-model="updateTemplateInfo.llmModelInfo.maxToken" :min="llm_maxToken_min" :max="llm_maxToken_max" :step="llm_maxToken_step" style="width: 60%; margin-left: 20px"></el-slider>
				</el-form-item>

				<el-form-item label="Temperature">
					<el-tooltip class="item" effect="dark" :content="$t('tip.llm_temperature')" placement="top">
						<span class="el-icon-question"></span>
					</el-tooltip>
					<el-slider v-model="updateTemplateInfo.llmModelInfo.temperature" :min="llm_temperature_min" :max="llm_temperature_max" :step="llm_temperature_step" style="width: 60%; margin-left: 20px"></el-slider>
				</el-form-item>

				<el-form-item label="Top p">
					<el-tooltip class="item" effect="dark" :content="$t('tip.llm_top_p')" placement="top">
						<span class="el-icon-question"></span>
					</el-tooltip>
					<el-slider v-model="updateTemplateInfo.llmModelInfo.topp" :min="llm_topp_min" :max="llm_topp_min_max" :step="llm_topp_step" style="width: 60%; margin-left: 20px"></el-slider>
				</el-form-item>
			</el-form>

			<div class="demo-drawer__footer" style="display: flex; margin-top: 40px; height: 40px">
				<el-button style="width: calc(50% - 20px); margin-left: 20px" @click="dis_update = false">{{ $t("button.return") }}</el-button>
				<el-button style="width: calc(50% - 20px); margin-right: 20px" type="primary" @click="updateTem">{{ $t("button.ok") }}</el-button>
			</div>
		</el-drawer>

		<!-- 删除模板 dialog -->
		<el-dialog :visible.sync="dis_delete" width="30%" :append-to-body="true">
			<span>{{ $t("chat.del_dialog") }}</span>
			<span slot="footer" class="dialog-footer">
				<el-button @click="dis_delete = false">{{ $t("button.return") }}</el-button>
				<el-button type="primary" @click="deleteTem">{{ $t("button.ok") }}</el-button>
			</span>
		</el-dialog>
	</div>
</template>

<script>
import { axios_instance } from "@/axios/index";

// 创建模板的默认模板
var defaultTemplate = {
	name: "",
	type: "",
	des: "This is a custom template.",
	hello: "Hello, please enter your question.",
	prompt: "请根据我提供的知识来回答问题，并列举知识中的数据详细回答。当所有知识内容都与问题无关时，你的回答必须包括“知识库中未找到您要的答案！”这句话。\n以下是我提供的知识：\n\n{knowledge}\n\n请根据这些知识回答我的问题:\n{question}\n",
	chatHistory: [],
	query_sample: [],
	dbInfoList: [],
	llmModelInfo: {
		maxToken: 500,
		modelName: "",
		temperature: 0.5,
		topp: 0,
	},
	retrieverModelInfo: {
		modelNameList: "",
		topk: 1,
    },
    knowledgeDiffSwitch:true,
    knowledgeDiffFunction:""
};

export default {
	data() {
		return {
			templateList: [],
			useTemplate: {},
			dis_add: false,
			dis_deploy: false,
			dis_update: false,
			dis_delete: false,
			// chat
			input: "",
			input_list: [],
			resStr: "",
			retrieverList: [],
			chatHisList: [],
			chat_loading: false,
			// add/update template
			order_type: "update",
			origin_updateTemplateInfo_name: "",
			updateTemplateInfo: defaultTemplate,
			templateTypeList: [],
			dbInfoSelectList: [],
			do_selectDbNameList: [],
			dbNameSelectList: [],
			llmModelSelectList: [],
            retrieverModelSelectList: [],
            knowledgeDiffFunction_list:[],
            // count
            select_parser_dbtype_count:0,
            select_parser_count: 0,
            select_text_count: 0,
            select_rule_nl_count:0,
            select_rule_nl_db_type_count:0,
            select_rule_code_count:0,
            select_rule_code_db_type_count:0,

			// 模板参数
			do_liner_flag: false,
			do_interface_flag: false,
			retriever_min: 1,
			retriever_max: 30,
			llm_topp_min: 0,
			llm_topp_min_max: 1,
			llm_topp_step: 0.01,
			llm_temperature_min: 0,
			llm_temperature_max: 1,
			llm_temperature_step: 0.01,
			llm_maxToken_min: 100,
			llm_maxToken_max: 4096,
			llm_maxToken_step: 1,
		};
	},

	mounted() {
		this.getTemplateList();
		let attempts = 0;
		const maxAttempts = 50;
		const intervalTime = 500;

		const intervalId = setInterval(() => {
			try {
				// 尝试执行代码
				if (this.templateList.length > 0) {
					this.clickTemplateItem(this.templateList[0]);
				}
				// 初始化 模板类型 列表
				axios_instance
					.get("/getTemplateTypeList")
					.then((res) => {
						this.templateTypeList = res.data.data;
					})
					.catch((err) => {});

				// 初始化 数据库信息 列表
				axios_instance
					.get("/getDataBaseData")
					.then((res) => {
						this.dbInfoSelectList = res.data.data;
						this.dbNameSelectList = this.dbInfoSelectList.map((item) => item.infoName);
					})
					.catch((err) => {});

				// 初始化 生成器模型 列表
				axios_instance
					.get("/getLlmDataList")
					.then((res) => {
						this.llmModelSelectList = res.data.data;
					})
					.catch((err) => {});

				// 请求结束

				// 如果执行成功，清除定时器
				clearInterval(intervalId);
				console.log("ok");
			} catch (error) {
				// 如果执行失败，增加尝试次数
				attempts++;
				// console.log(`尝试第 ${attempts} 次失败: ${error.message}`);
				// 如果达到最大尝试次数，清除定时器
				if (attempts >= maxAttempts) {
					clearInterval(intervalId);
					console.log("Stop execution when maximum number of attempts is reached.");
				}
			}
		}, intervalTime);
	},

	methods: {
		handleClose(done) {
			this.$confirm(this.$t("chat.close_ok"))
				.then((_) => {
					done();
				})
				.catch((_) => {});
		},

		scrollToBottom() {
			this.$nextTick(() => {
				const div = this.$refs.scrollableDiv;
				div.scrollTop = div.scrollHeight + 80;
			});
		},

		// 检查选择的知识库是否进行知识融合
        check_do_liner() {
            
            this.do_liner_flag = false;
            this.do_interface_flag = false;

			let dbInfoList = this.dbInfoSelectList.map((item) => [item.infoType, item.infoName]);
			dbInfoList = dbInfoList.filter((item) => this.do_selectDbNameList.includes(item[1]));
			if (dbInfoList.length == 0) {
				return;
			}

			for (let i in dbInfoList) {
				let item_root_type = dbInfoList[i][0][0];
				let item_type = dbInfoList[i][0][1];
				// console.log("🚀 -> item_type:\n", item_type);
				if (item_type == "Excel") {
					this.do_liner_flag = true;
				} else if (item_type == "Triple") {
					this.do_liner_flag = true;
                } else if (item_root_type == "Rule") {
					this.do_liner_flag = true;
                } else if (item_type.endsWith("DB")) {
					this.do_interface_flag = true;
                } 
                else {
				}
			}
		},

		clickTemplateItem(item) {
			this.useTemplate = item;
			this.input = "";

			this.input_list = [].concat(this.useTemplate["query_sample"]);

            this.do_selectDbNameList = this.useTemplate.dbInfoList.map((item) => item.infoName);
            
			let dbInfoList = this.dbInfoSelectList.map((item) => [item.infoType, item.infoName]);
			dbInfoList = dbInfoList.filter((item) => this.do_selectDbNameList.includes(item[1]));
            this.select_parser_dbtype_count = 0;
            this.select_rule_nl_db_type_count = 0;
            this.select_rule_code_db_type_count = 0;
            
            let temp_list = [];
            for(let i in dbInfoList){
                if (dbInfoList[i][0][1].endsWith("DB")) {
                    temp_list.push(dbInfoList[i][0][1]);
                }
                if (dbInfoList[i][0][1] == "Rule_NL" || dbInfoList[i][0][1] == "Rule_FOL") {
                    this.select_rule_nl_db_type_count += 1;
                }
                if (dbInfoList[i][0][1] == "Rule_Code") {
                    this.select_rule_code_db_type_count += 1;
                }

            }
            temp_list = [...new Set(temp_list)];

            this.select_parser_dbtype_count += temp_list.length;

            this.select_parser_count = 0;
            this.select_text_count = 0;
            this.select_rule_nl_count = 0;
            this.select_rule_code_count = 0;
            
            for(let i in this.updateTemplateInfo.retrieverModelInfo.modelNameList){
                if (this.updateTemplateInfo.retrieverModelInfo.modelNameList[i].endsWith("Parser")){
                    this.select_parser_count += 1;
                }
                if (this.updateTemplateInfo.retrieverModelInfo.modelNameList[i].endsWith("TEXT")){
                    this.select_text_count += 1;
                }
                if (this.updateTemplateInfo.retrieverModelInfo.modelNameList[i].endsWith("RuleNL")){
                    this.select_rule_nl_count += 1;
                }
                if (this.updateTemplateInfo.retrieverModelInfo.modelNameList[i].endsWith("RuleCode")){
                    this.select_rule_code_count += 1;
                }

            }
			console.log("🚀 -> this.do_selectDbNameList:\n", this.do_selectDbNameList);
			console.log("🚀 -> dbInfoList:\n", dbInfoList);

			let itemList = document.getElementsByClassName("template-list-item");
			for (let i in itemList) {
				try {
					itemList[i].style.backgroundColor = "#FFFFFF";
				} catch (error) {
					// console.log("🚀 -> itemList[i]:\n", itemList[i]);
				}
			}
			document.getElementById(item.name).style.backgroundColor = "#E8E8EA";
			this.chatHisList = item.chatHistory;
			console.log("🚀 -> this.chatHisList:\n", this.chatHisList);
			if (this.chatHisList.length == 0) {
				this.chatHisList.push({
					ctxs: [],
					text: this.useTemplate["hello"],
					role: "bot",
					id: this.chatHisList.length + 1,
				});
				item.chatHistory = [].concat(this.chatHisList);
				this.order_type = "update";
				this.updateTemplate(this.order_type, item, item.name);
			}

			this.check_do_liner();
		},

		updateTemplate(order, useTemplate, origin_template_name) {
			let param = {
				order: order,
				data: useTemplate,
				origin_template_name: origin_template_name,
			};
			axios_instance
				.post("/updateInitConfig", param)
				.then((res) => {
					this.templateList = res.data.data;
				})
				.catch((err) => {});
		},

		getTemplateList() {
			axios_instance
				.get("/getInitConfig")
				.then((res) => {
					this.templateList = res.data.data;
				})
				.catch((err) => {
					console.log(err);
				});
		},

		changeSelectDbName(value) {
			// console.log("🚀 -> value:\n", value)
			let dbInfoList = this.dbInfoSelectList.map((item) => [item.infoType, item.infoName]);
			dbInfoList = dbInfoList.filter((item) => this.do_selectDbNameList.includes(item[1]));

			console.log("🚀 -> this.do_selectDbNameList:\n", this.do_selectDbNameList);
			console.log("🚀 -> dbInfoList:\n", dbInfoList);

            this.select_parser_dbtype_count = 0;
            this.select_rule_nl_db_type_count = 0;
            this.select_rule_code_db_type_count = 0;

            let temp_list = [];
            for(let i in dbInfoList){
                if (dbInfoList[i][0][1].endsWith("DB")) {
                    temp_list.push(dbInfoList[i][0][1]);
                }
                if (dbInfoList[i][0][1] == "Rule_NL" || dbInfoList[i][0][1] == "Rule_FOL") {
                    this.select_rule_nl_db_type_count += 1;
                }
                if (dbInfoList[i][0][1] == "Rule_Code") {
                    this.select_rule_code_db_type_count += 1;
                }
                
            }
            temp_list = [...new Set(temp_list)];
            this.select_parser_dbtype_count += temp_list.length;
			this.updateTemplateInfo.retrieverModelInfo.modelNameList = [];
			this.check_do_liner();
		},

		getRetrieverList(flag) {
			if (flag == true) {
				// 查找完整路径
				let dbInfoList = this.dbInfoSelectList.map((item) => [item.infoType, item.infoName]);
				dbInfoList = dbInfoList.filter((item) => this.do_selectDbNameList.includes(item[1]));
				dbInfoList = dbInfoList.map((item) => item[0]);

				console.log("🚀 -> dbInfoList:\n", dbInfoList);
				axios_instance
					.post("/getRetrieverDataListByDB", { dbInfoList: dbInfoList })
					.then((res) => {
						this.retrieverModelSelectList = res.data.data;
					})
					.catch((err) => {});
			} else {
				this.retrieverModelSelectList = [];
			}
		},

		getknowledgeDiffFunction(flag) {
			if (flag == true) {

				axios_instance
					.get("/getknowledgeDiffFunction")
					.then((res) => {
						this.knowledgeDiffFunction_list = res.data.data;
					})
					.catch((err) => {});
			} else {
				this.knowledgeDiffFunction_list = [];
			}
		},



        changeSelectRetriever(value) {
            console.log("🚀 -> value:\n", value)
            console.log("🚀 -> this.updateTemplateInfo.retrieverModelInfo.modelNameList:\n", this.updateTemplateInfo.retrieverModelInfo.modelNameList)

            let text_flag = 0
            let parser_flag = 0

            for(let i in value){
                if(value[i].endsWith("TEXT")){
                    text_flag += 1
                }else if(value[i].endsWith("Parser")){
                    parser_flag += 1
                }else{
                    
                }
            }

            this.select_parser_count = 0;
            this.select_text_count = 0;
            this.select_rule_nl_count = 0;
            this.select_rule_code_count = 0;

            for(let i in value){
                if (value[i].endsWith("Parser")){
                    this.select_parser_count += 1;
                }
                if (value[i].endsWith("TEXT")){
                    this.select_text_count += 1;
                }
                if (value[i].endsWith("RuleNL")){
                    this.select_rule_nl_count += 1;
                }
                if (value[i].endsWith("RuleCode")){
                    this.select_rule_code_count += 1;
                }

            }
            
            if (text_flag > 1) {
                this.updateTemplateInfo.retrieverModelInfo.modelNameList.pop();
                this.$message({
                    message: this.$t("template.retriever_check"),
                    type: "warning",
                    duration: 2000,
                });
            }


		},

		pre_add_template() {
			this.origin_updateTemplateInfo_name = "";
			this.do_selectDbNameList = [];
			this.updateTemplateInfo = JSON.parse(JSON.stringify(defaultTemplate));
			this.dis_update = true;
			this.order_type = "add";
		},

		// click template
		pre_click_template(info, type) {
			this.useTemplate = info;
			this.updateTemplateInfo = JSON.parse(JSON.stringify(info));
			if (type == "deploy") {
				this.dis_deploy = true;
			} else if (type == "update") {
				this.origin_updateTemplateInfo_name = info.name;
				this.dis_update = true;
				this.order_type = "update";
			} else if (type == "delete") {
				this.dis_delete = true;
			}
		},

		// 部署模板
		deployTem() {
			this.dis_deploy = false;
			let msg = this.$message({
				message: this.$t("chat.deploy_show"),
				type: "info",
				duration: 0,
			});
			this.order_type = "deploy";
			this.do_chat(this.order_type, msg);
		},

		// 添加/更新模板
		updateTem() {
			// 转换
			let selectDbInfo = this.dbInfoSelectList.filter((item) => this.do_selectDbNameList.includes(item.infoName));
			this.updateTemplateInfo.dbInfoList = [].concat(selectDbInfo);

			// 校验
			if (this.updateTemplateInfo.name == "") {
				this.$message({
					message: this.$t("template.name_not_none"),
					type: "warning",
					duration: 1500,
				});
				return;
			}
			// name 不能重复
			for (let i = 0; i < this.templateList.length; i++) {
				if (this.templateList[i].name == this.updateTemplateInfo.name && this.origin_updateTemplateInfo_name != this.updateTemplateInfo.name) {
					this.$message({
						message: this.$t("template.name_not_repeat"),
						type: "warning",
						duration: 1500,
					});
					return;
				}
			}

			if (this.updateTemplateInfo.type == "") {
				this.$message({
					message: this.$t("template.type_not_none"),
					type: "warning",
					duration: 1500,
				});
				return;
			}
			if (this.updateTemplateInfo.dbInfoList.length == 0) {
				this.$message({
					message: this.$t("template.db_not_none"),
					type: "warning",
					duration: 1500,
				});
				return;
			}
			if (this.updateTemplateInfo.retrieverModelInfo.modelNameList.length == 0) {
				this.$message({
					message: this.$t("template.retriever_not_none"),
					type: "warning",
					duration: 1500,
				});
				return;
			}
			if (this.updateTemplateInfo.llmModelInfo.modelName == "") {
				this.$message({
					message: this.$t("template.llm_not_none"),
					type: "warning",
					duration: 1500,
				});
				return;
			}

            if (this.select_parser_count != this.select_parser_dbtype_count) {
				this.$message({
					message: this.$t("template.parser_check"),
					type: "warning",
					duration: 2000,
				});
				return;
            }

            let has_text_db_flag = false;
            for (let i in selectDbInfo) {
                console.log(selectDbInfo[i]);
                if(selectDbInfo[i]['infoType'][1] == "TextFile" || selectDbInfo[i]['infoType'][1] == "Excel" || selectDbInfo[i]['infoType'][1] == "Triple"){
                    has_text_db_flag = true;
                }else if(selectDbInfo[i]['infoType'][0] == 'Rule'){
                }else{
                }
            }
            if (has_text_db_flag == true && this.select_text_count <= 0) {
				this.$message({
					message: this.$t("template.text_retriever_mustselect"),
					type: "warning",
					duration: 2000,
				});
				return;
            }
            if (this.select_rule_nl_db_type_count>0 && this.select_rule_nl_count <= 0) {
				this.$message({
					message: this.$t("template.rule_nl_retriever_mustselect"),
					type: "warning",
					duration: 2000,
				});
				return;
            }
            if (this.select_rule_code_db_type_count>0 && this.select_rule_code_count <= 0) {
				this.$message({
					message: this.$t("template.rule_code_retriever_mustselect"),
					type: "warning",
					duration: 2000,
				});
				return;
            }

            if (this.updateTemplateInfo['knowledgeDiffFunction'] == "") {
				this.$message({
					message: this.$t("template.knowledgeDiffFunction_mustselect"),
					type: "warning",
					duration: 2000,
				});
				return;
            }

            // this.updateTemplateInfo.retrieverModelInfo.modelNameList = this.updateTemplateInfo.retrieverModelInfo.modelNameList.map((item) => item.split("/")[0]);

			console.log("🚀 -> this.updateTemplateInfo:\n", this.updateTemplateInfo);
			console.log("🚀 -> selectDbInfo:\n", selectDbInfo);

			// 更新
			this.updateTemplate(this.order_type, this.updateTemplateInfo, this.origin_updateTemplateInfo_name);
			this.$message({
				message: this.$t("chat.update_ok"),
				type: "success",
				duration: 1500,
			});
			this.dis_update = false;
		},
		// 删除模板
		deleteTem() {
			this.order_type = "delete";
			this.updateTemplate(this.order_type, this.useTemplate, this.useTemplate.name);
			this.dis_delete = false;
			this.$message({
				message: this.$t("chat.del_ok"),
				type: "success",
				duration: 1500,
			});
			if (this.templateList.length > 0) {
				this.clickTemplateItem(this.templateList[0]);
			}
		},

		// 对话
		do_chat(type, msg) {
			let param = {
				input: this.input,
				templateInfo: this.useTemplate,
			};
			if (type == "deploy") {
				param["input"] = "INITKNOWLEDGEANDMODELANDDEPLOY";
			}
			if (param["input"] == "") {
				this.$message({
					message: this.$t("chat.input_not_none"),
					type: "warning",
					duration: 1500,
				});
				return;
			}
			if (type != "deploy") {
				this.chat_loading = true;
				this.chatHisList.push({
					ctxs: [],
					text: this.input,
					role: "user",
					id: this.chatHisList.length + 1,
				});
				this.scrollToBottom();
			}
			this.input = "";
			axios_instance
				.post("/do_chat", param, { timeout: 0 })
				.then((res) => {
					if (res.data.code == 200) {
						if (type == "deploy") {
							// 部署会做的事
							msg.close();
							this.$message({
								message: this.$t("chat.deploy_ok"),
								type: "success",
								duration: 2000,
							});
						} else {
							// 正常chat会做的事
							this.chatHisList.push({
								ctxs: res.data.data["ctxs"],
								text: res.data.data["content"],
								role: "bot",
								id: this.chatHisList.length + 1,
							});
							this.chat_loading = false;
							this.useTemplate.chatHistory = [].concat(this.chatHisList);
							this.order_type = "update";
							this.updateTemplate(this.order_type, this.useTemplate, this.useTemplate.name);
							this.scrollToBottom();
						}
					} else {
						if (type == "deploy") {
							// 部署会做的事
							msg.close();
							this.$message({
								message: this.$t("chat.deploy_err"),
								type: "error",
								duration: 2000,
							});
						} else {
							// 正常chat会做的事
							this.chatHisList.push({
								ctxs: [],
								text: res.data.data,
								role: "bot",
								id: this.chatHisList.length + 1,
							});
							this.chat_loading = false;
							this.useTemplate.chatHistory = [].concat(this.chatHisList);
							this.order_type = "update";
							this.updateTemplate(this.order_type, this.useTemplate, this.useTemplate.name);
							this.scrollToBottom();
						}
					}
				})
				.catch((err) => {});
		},

		// 清除该模板的对话记录
		clearTemChatHis() {
			this.chatHisList = [];
			this.useTemplate.chatHistory = [];
			this.order_type = "update";
			this.updateTemplate(this.order_type, this.useTemplate, this.useTemplate.name);
		},
	},
};
</script>

<style scoped>
.el-form-item__content {
	display: flex;
	align-items: center;
	margin-right: 30px;
}
.el-form-item__label {
	width: 150px !important;
}

.chatroot {
	width: 100%;
	height: calc(100vh - 100px);
	display: flex;
}

.templatediv {
	width: 260px;
	height: calc(100% - 5px);
	margin-left: 5px;
	display: flex;
	flex-direction: column;
	overflow-y: auto;
}
.template-divider {
	height: 100%;
}
.template-list {
	display: flex;
	flex-direction: column;
	/* background-color: aqua; */
	margin-right: 10px;
	margin-left: 5px;
}
.template-list-item {
	margin-bottom: 20px;
	height: 90px;
	border-radius: 15px;
	padding: 11px;
	border: solid 2px #f0f0f0;
	display: flex;
	/* flex-direction: column; */
	overflow: hidden;
	border-radius: 10px; /* 圆角 */
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1), 0 6px 20px rgba(0, 0, 0, 0.1); /* 阴影效果 */
	transition: transform 0.3s, box-shadow 0.3s; /* 过渡效果 */
	border-top: 0.4px solid #ebebeb; /* 上边框颜色和厚度 */
}
.template-list-item:hover {
	transform: translateY(-10px); /* 悬停时上移 */
	box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2), 0 12px 40px rgba(0, 0, 0, 0.2); /* 悬停时阴影加深 */
}

.chatdiv {
	width: 100%;
	/* height: calc(100% - 50px); */
	max-height: calc(100% - 50px);
	margin-left: 15px;
	margin-right: 5px;
	background-color: #ffffff;
	display: flex;
	flex-direction: column;
}
.chat-res {
	display: flex;
	justify-content: center;
	height: 100%;
}
.chat-res-dev {
	width: calc(100% - 0px);
	height: calc(100% - 100px);
	max-height: calc(100% - 100px);

	margin-top: 30px;
	/* border: solid 2px #f0f0f0; */
	border-radius: 15px;
	/* background-color: #f0f0f0; */
	padding: 20px;
	overflow-y: auto;
	display: flex;
	flex-direction: column;
	scroll-behavior: smooth; /* 添加平滑滚动效果 */
}

.chat-res-dev-item-bot-logo {
	float: left;
	background-image: url("../static/bot.png");
	background-size: cover; /* 或者使用 contain */
	background-repeat: no-repeat; /* 防止背景图片重复 */
	background-position: center; /* 将背景图片居中 */
	height: 80px;
	width: 45px;
}
.chat-res-dev-item-bot {
	float: left;
	margin-left: 15px;
	max-width: 70%;
	background-color: #dbe2ef;
	padding: 15px;
	border-radius: 15px;
	overflow-y: auto;
	white-space: pre-wrap; /* 保留换行符和空白符 */
	margin-top: 50px;
	font-family: "Trebuchet MS", "Lucida Sans Unicode", "Lucida Grande", "Lucida Sans", Arial, sans-serif;
	line-height: 28px;
}

.chat-res-dev-item-user-logo {
	float: right;
	background-image: url("../static/user.png");
	background-size: cover; /* 或者使用 contain */
	background-repeat: no-repeat; /* 防止背景图片重复 */
	background-position: center; /* 将背景图片居中 */
	height: 80px;
	width: 70px;
}
.chat-res-dev-item-user {
	float: right;
	margin-right: 15px;
	max-width: 40%;
	background-color: #e6f4ff;
	padding: 15px;
	border-radius: 15px;
	overflow-y: auto;
	white-space: pre-wrap; /* 保留换行符和空白符 */
	margin-top: 50px;
	font-family: "Trebuchet MS", "Lucida Sans Unicode", "Lucida Grande", "Lucida Sans", Arial, sans-serif;
	line-height: 23px;
}

.chat-input {
	display: flex;
	width: 100%;
	justify-content: center;
}

.el-icon-delete-solid {
	text-align: center;
	transform: scale(1.5); /* 等比放大1.5倍 */
	margin: auto;
	margin-left: 0px;
	margin-right: 30px;
}

/* 整个滚动条 */
::-webkit-scrollbar {
	width: 5px; /* 滚动条的宽度 */
	height: 12px; /* 滚动条的高度 */
}

/* 滚动条的轨道 */
::-webkit-scrollbar-track {
	background: #dcdfe6; /* 轨道的背景色 */
	border-radius: 10px; /* 轨道的圆角 */
}

/* 滚动条上的滑块 */
::-webkit-scrollbar-thumb {
	background: #dcdfe6; /* 滑块的背景色 */
	border-radius: 10px; /* 滑块的圆角 */
}

/* 滑块在悬停时的样式 */
::-webkit-scrollbar-thumb:hover {
	background: #e8e8ea; /* 悬停时滑块的背景色 */
}
</style>
