import http from 'k6/http';
import { htmlReport } from "./k6-reporter/dist/bundle.js";
import { check, sleep } from "k6";

import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';



const img1 = open('./images/img1.jpg', 'b');
const img2 = open('./images/img2.jpg', 'b');
const img3 = open('./images/img3.jpg', 'b');
const img4 = open('./images/img4.jpg', 'b');
const img5 = open('./images/img5.jpg', 'b');
const img6 = open('./images/img6.png', 'b');
const img7 = open('./images/img7.png', 'b');
const img8 = open('./images/img8.jpg', 'b');
const img9 = open('./images/img9.jpg', 'b');

const url = 'https://mirindaflavourgenerator-com-backend.wspuat.com/api/cans/generate-from-links?ai=collage';



export const options = {

    stages: [
        { duration: '1m', target: 10 }, // traffic ramp-up from 1 to 100 users over 5 minutes.
        { duration: '2m', target: 10 }, // stay at 10 users for 10 minutes
        { duration: '1m', target: 0 }, // ramp-down to 0 users
    ],

};

export default function () {

    const fd = new FormData();
    fd.append('uploaded_images', http.file(img1, './images/img1.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img3, './images/img3.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img2, './images/img2.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img4, './images/img4.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img5, './images/img5.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img6, './images/img6.png', 'image/png'));
    fd.append('uploaded_images', http.file(img7, './images/img7.png', 'image/png'));
    fd.append('uploaded_images', http.file(img8, './images/img8.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img9, './images/img9.jpg', 'image/jpeg'));
    fd.append('flavour', 'orange');
    fd.append('image_descriptions', 'mirinda');
    fd.append('image_descriptions', 'mirinda');
    fd.append('image_descriptions', 'mirinda');
    fd.append('image_descriptions', 'mirinda');
    fd.append('image_descriptions', 'mirinda');
    fd.append('image_descriptions', 'mirinda');
    fd.append('image_descriptions', 'mirinda');
    fd.append('image_descriptions', 'mirinda');
    fd.append('image_descriptions', 'mirinda');

    const res = http.post('https://mirindaflavourgenerator-com-backend.wspuat.com/api/cans/upload-and-generate?ai=collage', fd.body(), {
        headers: { 'Content-Type': 'multipart/form-data; boundary=' + fd.boundary },
    });
    console.log("res.body --- first request", res.body);

    let data = {
        "selectedImagesUrls": ["https://i.imgur.com/cev7sDR.jpeg",
            "https://i.imgur.com/OYxU07m_d.jpg",
            "https://i.imgur.com/rs8VLkc.jpeg",
            "https://i.imgur.com/5bEj6z6.webp",
            "https://i.imgur.com/eTxzk46_d.webp?maxwidth=760&fidelity=grand"],

        "imageDescriptions": ["mirinda", "mirinda", "mirinda", "mirinda", "mirinda"],
        "flavour": "orange",
        "recaptchaToken": "",
        "market": ""
    }

    // Using a JSON string as body
    const res2 = http.post(url, JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    console.log("res.body --- second request", res2.body); 
}

export function handleSummary(data) {
    return {
      "summary.html": htmlReport(data),
    };
  }

