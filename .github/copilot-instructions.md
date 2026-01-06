# Copilot 使用说明（项目特定）

目的：帮助 AI 编码代理快速理解本仓库的架构、关键工作流、约定和集成点，以便高质量地修改/生成代码。

概览
- 这是一个基于 Electron + Vite 的桌面应用（前端使用 React + TypeScript），辅助工具在 `python/` 目录提供本地 Flask API 用于与 WeChat 自动化交互。
- 主要运行时边界：Electron 主进程（`electron/main.ts`）↔ 预加载脚本（`preload.mjs`）↔ 渲染进程（`src/`）；以及独立的 Python 进程（`python/api_server.py`）通过 HTTP 提供服务。

关键文件与位置（举例）
- Electron 主进程：[electron/main.ts](electron/main.ts)
- 预加载（主进程暴露 API）：[dist-electron/preload.mjs](dist-electron/preload.mjs)（构建产物）或源文件 `electron/preload.ts`
- 渲染进程入口：[src/main.tsx](src/main.tsx)、[src/App.tsx](src/App.tsx)
- 构建脚本与依赖：[package.json](package.json)
- Python 本地 API：[python/api_server.py](python/api_server.py)、自动化模块如 `python/wechat_auto.py`（在 `python/` 下）

快速可执行命令
- 前端开发（仅启动 Vite 开发服务器）: `npm run dev`
- 打包（TypeScript 编译 + Vite 构建 + electron-builder）: `npm run build`
- 代码检查: `npm run lint`
- 启动 Python API（示例）: 在虚拟环境中运行 `python python/api_server.py`（默认监听 5000 端口）

重要架构细节（对 AI 很重要）
- `electron/main.ts` 使用 `VITE_DEV_SERVER_URL` 环境变量来判断是否载入 dev server（开发时先运行 `npm run dev`，并在另一个进程中以该 URL 启动 Electron 可实现热加载）。如果实现跨进程开发自动化，请保留此逻辑。
- 渲染进程通过 `preload.mjs`/contextBridge 暴露的 IPC 接口与主进程通信。示例：`src/main.tsx` 中监听 `main-process-message`。
- 构建产物分两部分：渲染器在 `dist/`，Electron 主进程在 `dist-electron/`。`package.json` 的 `main` 指向 `dist-electron/main.js`。
- 仓库使用 ESM（`type: module`），请用 `import` 语句，遵循现有模块风格。

Python/WeChat 注意事项
- `python/api_server.py` 使用 `comtypes` 与 Windows COM（WeChat 自动化）交互：只能在 Windows 环境下运行并且需要 `comtypes` 等本地依赖。请不要在非 Windows 环境下尝试直接运行这些自动化代码。
- API 默认端口：5000。渲染或 Electron 端如果调用该 API，请确认跨域（CORS）与进程安全性。

工程约定与小细节
- 使用 TypeScript + tsc 编译（`npm run build` 会先运行 `tsc`）。修改类型定义时请同步 `tsconfig.json`。
- 前端样式使用 Tailwind；样式配置位于 `tailwind.config.js`。
- 代码质量：有 ESLint 配置，提交大改动前运行 `npm run lint`。
- 不要随意更改 `preload` 暴露的接口；渲染端直接调用 `window.ipcRenderer` 的模式在 `src/` 已被使用。

对 AI 的具体建议（可操作模板）
- 修改 UI：在 `src/components/` 下查找对应组件并调整。先运行 `npm run dev` 在浏览器中验证样式/行为，再打包测试 Electron 集成。
- 增加 Electron 主进程功能：编辑 `electron/main.ts`，注意 `VITE_DEV_SERVER_URL` 分支并在开发时同时运行 renderer/server。
- 修改或扩展 Python API：编辑 `python/api_server.py` 或 `python/wechat_auto.py`，在 Windows 虚拟环境中运行并测试。确保 `comtypes` 已安装并且手工验证 WeChat 自动化步骤。

限制与危险点（不要幻想不可见信息）
- WeChat 自动化涉及系统级 COM 操作；在修改或自动化测试时请附带明确的运行平台指令并询问用户授权。
- 构建与打包会触发 `electron-builder`，这会访问本机构建工具链；不要在 CI 上盲目运行打包，除非已配置证书/环境。

后续：已基于仓库现状起草本文件。如需把内容合并到已有指南或补充更多运行示例（例如开发时如何并行启动 Electron + Vite + Python），请告诉我，我会迭代更新。
