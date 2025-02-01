import http from 'k6/http';
import { htmlReport } from "./k6-reporter/dist/bundle.js";
import { check, sleep } from "k6";

export const options = {
    vus: 3,
    duration: '3m'
  };

export default function () {
  const url = 'https://dewinstalvlup-com.wspprod.com/get_user_status';
  const payload = JSON.stringify({
    id: '5671141046345824'
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  http.post(url, payload, params);
}

// export default function () {
//   const res = http.get('https://dewinstalvlup-com.wspprod.com/');
// }

export function handleSummary(data) {
    return {
      "summary.html": htmlReport(data),
    };
  }