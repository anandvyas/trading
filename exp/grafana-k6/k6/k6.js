import http from 'k6/http';
import exec from 'k6/execution';
import { check } from 'k6';
import { sleep } from 'k6';
import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';

const img1 = open('img1.jpg', 'b');
const img2 = open('img2.jpg', 'b');
const img3 = open('img3.jpg', 'b');
const img4 = open('img4.jpg', 'b');
const img5 = open('img5.jpg', 'b');
const img6 = open('img6.png', 'b');
const img7 = open('img7.png', 'b');
const img8 = open('img8.jpg', 'b');
const img9 = open('img9.jpg', 'b');
const url = 'https://mirindaflavourgenerator-com-backend.wspuat.com/api/cans/generate-from-links?ai=collage';

export const options = {
//for avg load test in this section
    stages: [
        { duration: '30s', target: 1 }, // traffic ramp-up from 1 to 100 users over 5 minutes.
        { duration: '2m', target: 15  }, // stay at 100 users for 10 minutes
        { duration: '3m', target: 30 }, // ramp-down to 0 users
    ],
};

// { duration: '10m', target: 2 }, // stay at 100 users for 10 minutes

export default function () {
    const fd = new FormData();
    fd.append('uploaded_images', http.file(img1, 'img1.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img2, 'img2.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img3, 'img3.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img4, 'img4.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img5, 'img5.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img6, 'img6.png', 'image/png'));
    fd.append('uploaded_images', http.file(img7, 'img7.png', 'image/png'));
    fd.append('uploaded_images', http.file(img8, 'img8.jpg', 'image/jpeg'));
    fd.append('uploaded_images', http.file(img9, 'img9.jpg', 'image/jpeg'));
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

    //fd.append('images', http.file(img2, 'test.jpg', 'image/jpeg'));
    //fd.append('text', http.file(txt, 'text.txt', 'text/plain'));
    const res = http.post('https://3278-mirinda-ai-can-backend-staging.unit9.net/api/cans/upload-and-generate?ai=collage', fd.body(), {
         headers: { 'Content-Type': 'multipart/form-data; boundary=' + fd.boundary },
    });
    console.log(
        "/api/upload-and-generate",
        res.status, '\n',
        "Sending duration:", parseFloat(res.timings.sending / 1000).toFixed(2), 'seconds', '\n',
        "Waiting duration:", parseFloat(res.timings.waiting / 1000).toFixed(2), 'seconds', '\n',
        "Receiving duration:", parseFloat(res.timings.receiving / 1000).toFixed(2), 'seconds', '\n',
        "Total duration: ", parseFloat(res.timings.duration / 1000).toFixed(2), '\n',
        "VU ID:", exec.vu.idInInstance, '\n',
        "iteration:", exec.vu.iterationInScenario, '\n',
    );

    let data = {
        "selectedImagesUrls": ["https://i.imgur.com/cev7sDR.jpeg","https://i.imgur.com/OYxU07m_d.jpg","https://i.imgur.com/rs8VLkc.jpeg","https://i.imgur.com/5bEj6z6.webp","https://i.imgur.com/eTxzk46_d.webp?maxwidth=760&fidelity=grand" ],
        "imageDescriptions": ["mirinda","mirinda","mirinda","mirinda","mirinda"],
        "flavour": "orange",
        "recaptchaToken": "",
        "market": ""
    }
    //sleep(2)
    // Using a JSON string as body
    const res2 = http.post(url, JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    console.log(
        "/api/generate-from-links",
        res2.status, '\n',
        "Sending duration:", parseFloat(res2.timings.sending / 1000).toFixed(2), 'seconds', '\n',
        "Waiting duration:", parseFloat(res2.timings.waiting / 1000).toFixed(2), 'seconds', '\n',
        "Receiving duration:", parseFloat(res2.timings.receiving / 1000).toFixed(2), 'seconds', '\n',
        "Total duration: ", parseFloat(res2.timings.duration / 1000).toFixed(2), '\n',
        "VU ID:", exec.vu.idInInstance, '\n',
        "iteration:", exec.vu.iterationInScenario, '\n',
    );


// sleep(2)
}
