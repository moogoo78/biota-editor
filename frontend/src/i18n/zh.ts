import type { Dict } from "./en";

const zh: Dict = {
  app: { name: "BiotaEditor", tagline: "TaiCOL 名錄編輯器" },
  auth: {
    login: "登入", signup: "建立帳號", logout: "登出", email: "Email", password: "密碼", name: "姓名",
    emailHint: "請使用 TaiCOL 名錄工具帳號的 Email——名錄依此比對。",
    toSignup: "還沒有帳號？建立一個", toLogin: "已有帳號？登入",
  },
  pubs: {
    title: "出版物", empty: "尚無出版物。請在 TaiCOL 名錄工具發布名錄，或手動匯入。",
    import: "匯入名錄", namespaceId: "名錄 ID", available: "你的 TaiCOL 名錄", imported: "已匯入",
    open: "開啟", items: "{{n}} 個名稱", synced: "同步於 {{at}}", delete: "刪除",
    confirmDelete: "確定刪除此出版物與已選的標本、影像？",
    loadAvailable: "無法自 TaiCOL 取得名錄清單——請直接輸入 ID。",
  },
  status: { draft: "草稿", review: "審閱中", done: "完成" },
  editor: {
    back: "出版物", sync: "自 TaiCOL 同步", syncing: "同步中…",
    synced: "已同步：新增 {{created}}、更新 {{updated}}、移除 {{deleted}}",
    export: "匯出", preview: "預覽", hidePreview: "隱藏預覽", literatures: "文獻", keys: "檢索表",
    pick: "請從左側選擇名稱", filter: "篩選名稱…", title: "標題", author: "作者", save: "儲存",
    saved: "已儲存", cancel: "取消", addLit: "新增文獻",
  },
  tabs: { text: "文字", specimens: "標本", images: "影像" },
  text: {
    common_names: "俗名（以 | 分隔）", description: "描述", distribution: "分布", note: "附註",
    synonyms: "異名", edited: "已在本地修改", revert: "還原為 TaiCOL", usage: "學名用法", noSynonyms: "無異名",
  },
  spec: {
    picked: "已選標本（{{n}}）", candidates: "來自 TBIA 標本註記平台", byNames: "依學名", byText: "全文",
    search: "搜尋", names: "比對學名", none: "尚未選擇標本。", noResults: "沒有符合的標本。",
    total: "{{n}} 筆", add: "加入", added: "已加入", remove: "移除", more: "載入更多", county: "縣市",
    typeStatus: "模式標本", dataset: "資料集", hasMedia: "有影像", open: "在 ISLAND 開啟",
    reset: "重設文字", upstreamDown: "標本 API 無法連線：{{msg}}", clearFilters: "清除篩選",
  },
  img: {
    picked: "已選影像（{{n}}）", source: "來源", inat: "iNaturalist", taieol: "臺灣生命大百科",
    none: "尚未選擇影像。", noResults: "找不到影像。", more: "載入更多", caption: "圖說",
    noLicense: "非 CC 授權——發布前請確認", nameOverride: "搜尋學名", taxon: "TaiCOL 物種 {{id}}",
    open: "來源頁面",
  },
  keys: {
    new: "新增檢索表", title: "檢索表標題", number: "號", indent: "縮排", description: "敘述",
    goto: "→ 跳至", result: "→ 名稱", addEntry: "新增敘述", delete: "刪除檢索表", empty: "尚無檢索表。",
  },
  notif: { title: "通知", empty: "沒有新通知", markRead: "標為已讀" },
  common: { loading: "載入中…", error: "錯誤：{{msg}}", up: "上移", down: "下移", drag: "拖曳排序" },
};
export default zh;
