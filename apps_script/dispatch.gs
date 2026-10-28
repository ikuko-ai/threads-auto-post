/**
 * Threads自動投稿の精密トリガー（スプレッドシートにバインドしたApps Script）
 *
 * GitHub Actionsのcron(schedule)は大幅に遅延するため、
 * このスクリプトが5分ごとにシート1を見て、投稿時刻が来た未投稿行があれば
 * GitHub APIで post.yml を workflow_dispatch で起動する。
 *
 * 初回セットアップ（1回だけ）:
 *   1. 拡張機能 > Apps Script で本ファイルを貼り付ける
 *   2. プロジェクトの設定 > スクリプト プロパティに GITHUB_TOKEN を追加
 *      （fine-grained PAT。対象リポジトリ ikuko-ai/threads-auto-post、Actions: Read and write）
 *   3. testDispatch を実行して接続確認（承認ダイアログを許可）
 *   4. setupTrigger を1回実行（5分ごとのトリガーが作成される）
 */

const REPO = 'ikuko-ai/threads-auto-post';
const WORKFLOW = 'post.yml';
const BRANCH = 'master';
const SHEET_NAME = 'シート1';
const WINDOW_MIN = 60;          // 予定時刻から何分以内の行を対象にするか
const THROTTLE_MS = 10 * 60 * 1000; // 連続起動の最短間隔（10分）

// 5分ごとに実行される本体
function checkAndDispatch() {
  // プロジェクトのタイムゾーン設定に依存せず、常に日本時間で判定する
  const now = new Date();
  const today = Utilities.formatDate(now, 'Asia/Tokyo', 'yyyy/MM/dd');
  const nowMin = toMinutes_(Utilities.formatDate(now, 'Asia/Tokyo', 'HH:mm'));

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) throw new Error('シート「' + SHEET_NAME + '」が見つかりません');
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  // 表示文字列で取得（Sheets APIの書式付き値と一致させる）
  const rows = sheet.getRange('A2:E' + lastRow).getDisplayValues();

  const due = rows.some(function (r) {
    const date = String(r[0]).trim();
    const time = String(r[1]).trim();
    const text = String(r[3]).trim();
    const status = String(r[4]).trim();
    if (date !== today || !text) return false;
    if (status === '投稿済' || status === 'スキップ') return false;
    const sched = toMinutes_(time);
    if (sched === null) return false;
    const diff = nowMin - sched; // 正なら予定時刻を過ぎている
    return diff >= -1 && diff <= WINDOW_MIN;
  });

  if (!due) return;

  // 連続起動の抑止（前回起動から10分以内なら見送る）
  const props = PropertiesService.getScriptProperties();
  const last = Number(props.getProperty('lastDispatchAt') || 0);
  if (now.getTime() - last < THROTTLE_MS) {
    console.log('前回起動から10分以内のため見送り');
    return;
  }

  dispatch_();
  props.setProperty('lastDispatchAt', String(now.getTime()));
}

// 5分ごとのトリガーを作り直す（1回だけ実行すればよい）
function setupTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'checkAndDispatch') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('checkAndDispatch').timeBased().everyMinutes(5).create();
  console.log('トリガーを設定しました（5分ごと）');
}

// 接続テスト用：対象行・間隔制限を無視して1回起動する
function testDispatch() {
  dispatch_();
  console.log('テスト起動を送信しました');
}

// GitHub APIで post.yml を起動する
function dispatch_() {
  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  if (!token) {
    throw new Error('スクリプト プロパティ GITHUB_TOKEN が未設定です');
  }
  const url = 'https://api.github.com/repos/' + REPO + '/actions/workflows/' + WORKFLOW + '/dispatches';
  const res = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28'
    },
    payload: JSON.stringify({ ref: BRANCH }),
    muteHttpExceptions: true
  });
  const code = res.getResponseCode();
  if (code !== 204) {
    // 失敗時は例外にして、Apps Scriptの失敗通知メールで気付けるようにする
    throw new Error('GitHub起動に失敗 status=' + code + ' body=' + res.getContentText());
  }
  console.log('GitHub Actionsを起動しました (204)');
}

// "HH:MM" / "H:MM" を分に変換する（解釈できなければ null）
function toMinutes_(s) {
  const m = /^(\d{1,2}):(\d{2})/.exec(String(s).trim());
  if (!m) return null;
  return Number(m[1]) * 60 + Number(m[2]);
}
