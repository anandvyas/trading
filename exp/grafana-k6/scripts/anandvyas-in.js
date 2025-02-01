import http from "k6/http";
// import { htmlReport } from "https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: '30s', target: 100 },
    { duration: '1m30s', target: 200 },
    { duration: '20s', target: 0 },
  ],
};

export default function () {
  const res = http.get('https://dev-brands-cms.wspuat.com/');
  sleep(1);
  check(res, { 'status was 200': (r) => r.status == 200 });
}


// export function handleSummary(data) {
//   return {
//     "summary.html": htmlReport(data),
//   };
// }