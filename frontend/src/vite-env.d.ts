/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

/**
 * 扩展 Vite 的 ImportMetaEnv 接口，为自定义环境变量提供类型声明。
 * 新增变量时在此同步添加字段，确保 import.meta.env.xxx 有类型提示。
 */
interface ImportMetaEnv {
  /** 后端 API 基础地址，对应 .env 中的 VITE_API_BASE_URL */
  readonly VITE_API_BASE_URL: string
  /** 开发模式绕过登录认证，对应 .env 中的 VITE_DEV_BYPASS_AUTH */
  readonly VITE_DEV_BYPASS_AUTH: string
}

/**
 * 扩展 Vite 的 ImportMeta 接口，使 env 属性使用自定义的 ImportMetaEnv 类型。
 */
interface ImportMeta {
  readonly env: ImportMetaEnv
}
