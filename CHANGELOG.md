# 更新日誌 (Changelog)

## 2026-05-22
- **商品カード橙枠・qty-badge 残存バグ**：clearCart 或いは qty 1→0 でカートクリア後、商品カードの橙枠・qty-badge が残ったままになる → clearCart() と changeCartQty() の optimistic removal 後に `render()` 追加
- **購物車税額/合計 ¥0 リセットバグ修正**：`changeCartQty` で qty 1→0 の時に税額/合計が ¥0 にならない → 直接 DOM 操作で即座リセット（optimistic update）
- **clearCart() 同様修正**：fetch 前に DOM を ¥0 にリセット
- **order-complete も修正**：fetch 前に DOM を ¥0 にリセット
- **ブランド「全て表示」バグ修正**：`selectMaker('全て表示')` で全商品除外 → 空表示になる問題 → `activeMaker = (name === '全て表示' ? '' : name)` に修正
- **根本原因**：どちらもコードは正しかったが、**ブラウザキャッシュ**で旧 JS が読み込まれているように見えただけ。修正適用後、Ctrl+Shift+R → 隱身模式テスト → Clear site data の順で確認すること。

## 2026-05-20
- 全角表示対応：Modal / PDF印刷 / 注文履歴 details の商品名に NFKC 正規化（esc()関数）適用
- 掛率表示改善：`discount_rate < 1.0` → 「68%」、そうでない場合 → 「問合」
- CSV エクスポート 404修正：admin.html の URL を `/inventory-website/api/admin/export/` に変更
- CSV KeyError 修正：orders.json の `subtotal`/`tax` がない注文対応（`.get()` 方式）
- 管理者パスワード整合：admin.html と app.py の両方を `toyohaya` に統一
- Starserver 環境対応完了：PHP curl プロキシー + gunicorn 1 worker（session 共有）

## 2026-05-19
- 画像404解決：`.htaccess` に `/images/` rewrite ルールを追加しない（全リクエストを index.php に流す）
- session 不整合回避：gunicorn 1 worker 固定
- index.php str_replace 追加：`/static/images/` → `/inventory-website/static/images/`

## 2026-05-18
- Starserver デプロイ開始
- Flask gunicorn + PHP curl proxy 構成で構築