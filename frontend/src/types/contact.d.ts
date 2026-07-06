// ---------- 联系人（对应后端 ContactResponse） ----------

export interface ContactItem {
  id: number
  name: string
  emailAddress: string
  phone: string | null
  remark: string | null
}

// ---------- 联系人创建/更新请求（对应后端 ContactRequest） ----------

export interface ContactRequest {
  name: string
  emailAddress: string
  phone?: string
  remark?: string
}
