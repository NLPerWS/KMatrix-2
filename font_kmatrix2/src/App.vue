<template>
	<div id="app">
		<el-container>
			<el-header>
				<div class="leftroot">
					<div class="logo"></div>
					<div class="logotitle">
						<strong>KMatrix-2</strong>
					</div>
				</div>

				<div class="alignroot">
					<div class="link-item">
						<router-link to="/knowledgedb"
							><span class="el-icon-s-order"></span><strong>&nbsp;&nbsp;&nbsp;<span v-text="$t('header.zsk')"></span></strong
						></router-link>
					</div>
					<div class="link-item">
						<router-link to="/chat"
							><span class="el-icon-s-comment"></span><strong>&nbsp;&nbsp;&nbsp;<span v-text="$t('header.chat')"></span></strong
						></router-link>
					</div>
					<div class="link-item">
						<router-link to="/task"
							><span class="el-icon-s-cooperation"></span><strong>&nbsp;&nbsp;&nbsp;<span v-text="$t('header.task')"></span></strong
						></router-link>
					</div>


				</div>

				<div class="rightroot">
					<div class="language-select">
						<el-select v-model="language" @change="changeLanguage">
							<el-option value="zh" label="Chinese"></el-option>
							<el-option value="en" label="English"></el-option>
						</el-select>
					</div>
				</div>
			</el-header>

			<el-divider></el-divider>

			<el-main>
				<router-view />
			</el-main>
		</el-container>
	</div>
</template>

<script>
export default {
	data() {
		return {
			language: "en",
		};
	},

    mounted() {
        this.$i18n.locale = this.language;
        
		document.addEventListener("DOMContentLoaded", function () {
			const linkItems = document.querySelectorAll(".headerdiv .link-item");

			linkItems.forEach((item) => {
				item.addEventListener("click", function () {
					// 移除所有元素的选中状态
					linkItems.forEach((link) => link.classList.remove("selected"));
					// 为当前点击的元素添加选中状态
					this.classList.add("selected");
				});
			});
		});
	},

	methods: {
		changeLanguage(lang) {
			this.$i18n.locale = lang;
		},
	},
};
</script>

<style>

/* 整个滚动条 */
::-webkit-scrollbar {
	width: 6px; /* 滚动条的宽度 */
	height: 6px; /* 滚动条的高度 */
}

/* 滚动条的轨道 */
::-webkit-scrollbar-track {
	background: #dcdfe6; /* 轨道的背景色 */
	border-radius: 10px; /* 轨道的圆角 */
}

/* 滚动条上的滑块 */
::-webkit-scrollbar-thumb {
	background: #CACAD0; /* 滑块的背景色 */
	border-radius: 10px; /* 滑块的圆角 */
}

/* 滑块在悬停时的样式 */
::-webkit-scrollbar-thumb:hover {
	background: #CACAD0; /* 悬停时滑块的背景色 */
}



</style>

<style scoped>

.el-main{
    padding: 0px;
}
.el-divider--horizontal {
    display: block;
    height: 1px;
    width: 100%;
    margin: 10px 0;
}


.el-header {
	line-height: 40px;
	height: 40px;
	display: flex;
	justify-content: space-between;
	text-align: center;
}

.leftroot {
	display: flex;
}
.logo {
    background-image: url("../static/logo.png");
	/* background-color: antiquewhite; */
    width:80px;
	max-width: 80px;
    background-size: contain; /* 等比缩放，图片完全显示 */
    background-repeat: no-repeat; /* 防止图片重复 */
    background-position: center; /* 图片居中显示 */
}
.logotitle {
	margin-left: 25px;
	width: 80px;
	color:darkcyan;
	font-family: "Trebuchet MS", "Lucida Sans Unicode", "Lucida Grande", "Lucida Sans", Arial, sans-serif;
    font-style: italic;

	line-height: 70px;
	transition: transform 0.3s; /* 添加过渡效果 */
	transform: scale(2.1); /* 鼠标悬停时等比放大 */
}

.alignroot {
	text-align: center;
	line-height: 70px;
	display: flex;
	justify-content: center;
}
.link-item {
	height: 100%;
	padding: 5px;
	margin-left: 50px;
	border-radius: 15px;
	font-size: 1.05rem;
	color: black;
	transition: background-color 0.3s ease, color 0.3s ease;
	cursor: pointer;
	transition: background-color 0.3s, color 0.3s;
}
.link-item:hover {
	background-color: #4096ff; /* 选中时的背景色 */
	color: white; /* 选中时的字体颜色 */
}
a {
	text-decoration: none; /* 去掉下划线 */
	color: inherit; /* 继承父元素的颜色 */
}

.rightroot {
	display: flex;
	text-align: center;
	line-height: 70px;
}
.language-select {
	/* background-color: antiquewhite; */
	width: 200px;
}

/* .el-footer {
	text-align: center;
	line-height: 40px;
}
.el-main {
	min-height: calc(100vh - 80px);
} */
</style>
