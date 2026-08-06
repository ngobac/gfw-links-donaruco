# gfw-links-donaruco

Pipeline tự động tạo và duy trì link bản đồ Global Forest Watch (GFW) cho ~2.300 lô cao su, phục vụ truy xuất nguồn gốc EUDR.

## Sản phẩm bàn giao

`docs/links.json` — danh sách link GFW theo mã lô (`IDlomoi`), tự cập nhật hằng đêm.

Quy tắc đọc cho hệ thống truy xuất: lấy `long_url` theo `id_lo`; chỉ hiển thị khi `status` là `alive`/`healed`; `last_checked` thể hiện độ tươi dữ liệu.

## Cơ chế

- **SYNC** (01:00 VN hằng đêm): query toàn bộ lô từ AGOL Feature Layer, POST geostore GFW cho lô mới/đổi ranh, cập nhật `docs/links.json`.
- **HEAL** (08h/16h/24h VN): kiểm tra từng geostore còn sống; nếu bị xóa thì POST lại đúng GeoJSON — nhờ tính determinism của geostore v1, ID (và URL) không đổi.
- Biến động (lô mới, đổi ranh, lô bị xóa, link chết) báo qua Telegram.

## Cấu hình

Secrets cần khai báo trong Settings → Secrets and variables → Actions:
`AGOL_USERNAME`, `AGOL_PASSWORD`, `AGOL_LAYER_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

`map_template.txt` chứa phần query string cấu hình layer (Tree cover loss 2021→nay + Tree plantations). Khi GFW ra dữ liệu TCL năm mới (~tháng 4): cập nhật template, xóa `docs/links.json`, chạy tay SYNC để rebuild toàn bộ URL.
