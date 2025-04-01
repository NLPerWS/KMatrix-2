import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import legacy from '@vitejs/plugin-legacy';
import vue2 from '@vitejs/plugin-vue2';

export default defineConfig({
	base: "./",
	plugins: [
		vue2(),
		legacy({
			targets: ["ie >= 11"],
			additionalLegacyPolyfills: ["regenerator-runtime/runtime"],
		}),
	],
	resolve: {
		alias: {
			"@": fileURLToPath(new URL("./src", import.meta.url)),
		},
	},
	server: {
		// 是否开启 https
		https: false,
		// 端口号
		port: 10021,
		// 监听所有地址
		host: "0.0.0.0",
		// 服务启动时是否自动打开浏览器
		open: false,
		// 允许跨域
		cors: true,
		// 自定义代理规则
		proxy: {},
		watch: {
			ignored: ["**/node_modules/**", "**/.git/**"],
			usePolling: true, // 对某些文件系统有效
			followSymlinks: false,
			disableGlobbing: true,
			interval: 1000,
			binaryInterval: 3000,
			awaitWriteFinish: {
				stabilityThreshold: 2000,
				pollInterval: 100,
			},
		},
	},
	build: {
		// 设置最终构建的浏览器兼容目标
		target: "es2015",
		// 构建后是否生成 source map 文件
		sourcemap: false,
		//  chunk 大小警告的限制（以 kbs 为单位）
		chunkSizeWarningLimit: 2000,
		// 启用/禁用 gzip 压缩大小报告
		reportCompressedSize: false,
	},
});