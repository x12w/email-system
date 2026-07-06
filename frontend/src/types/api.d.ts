export interface ApiResponse<T> {
  code: string
  message: string
  data: T
}

export interface PaginatedData<T> {
  records: T[]
  page: number
  size: number
  total: number
}
