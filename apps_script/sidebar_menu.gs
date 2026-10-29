/**
 * 承認パネル（sidebar.html）のサーバー側処理
 *
 * シートを開くとメニュー「Threads投稿」が出る。
 * 「承認パネルを開く」で右側にパネルを表示し、選択中の行のE列（承認）を
 * OK / スキップ / 修正 に書き換える。修正の場合はF列の修正文が投稿される（post.py）。
 *
 * dispatch.gs と同じプロジェクトに置く（定数名が重ならないよう、ここでは定数を定義しない）。
 */

// シートを開いたときにメニューを追加する
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Threads投稿')
    .addItem('承認パネルを開く', 'showSidebar')
    .addToUi();
}

function showSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('sidebar').setTitle('投稿の承認');
  SpreadsheetApp.getUi().showSidebar(html);
}

// 投稿管理のシート（シート1）以外では操作させない
function approvalSheet_() {
  const sheet = SpreadsheetApp.getActiveSheet();
  return sheet.getName() === 'シート1' ? sheet : null;
}

// 選択中の行の内容をパネルに返す（1.5秒ごとに呼ばれる）
function getSelectedRow() {
  const sheet = approvalSheet_();
  if (!sheet) return null;
  const row = sheet.getActiveRange().getRow();
  if (row < 2) return null;
  // A:日付 B:時間 C:種類 D:投稿文 E:承認 F:修正後の投稿文
  const v = sheet.getRange(row, 1, 1, 6).getDisplayValues()[0];
  return { date: v[0], time: v[1], type: v[2], text: v[3], status: v[4] };
}

// 選択中の行のE列に承認状態を書き込む
function setApproval(value) {
  if (['OK', 'スキップ', '修正'].indexOf(value) === -1) {
    throw new Error('不明な値です: ' + value);
  }
  const sheet = approvalSheet_();
  if (!sheet) throw new Error('「シート1」で行を選択してください');
  const row = sheet.getActiveRange().getRow();
  if (row < 2) throw new Error('2行目以降を選択してください');
  if (sheet.getRange(row, 5).getDisplayValue() === '投稿済') {
    throw new Error('この行はすでに投稿済みです');
  }
  sheet.getRange(row, 5).setValue(value);
  return value;
}
