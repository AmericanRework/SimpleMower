//#!/usr/bin/env node
//welp. This code runs on the CLIENT not the SERVER. doh. ok. Writing to client filesystem is not allowed in javascript running in browser, and doesn't help us anyway. Use fetch: 
//may need to install fetch: npm install node-fetch


document.addEventListener('keypress', (event) => {
    const bodyElement = document.querySelector('body');
    const character = String.fromCharCode(event.charCode);
    var responseData;
    fetch('/writefile', {
        method: 'POST',
        headers: {
         'Content-Type': 'text/plain',
         },
        body: character,
        })
    .then((response) => response.text())
    .then((data) => {
    bodyElement.innerHTML = data; // Store response text to body of webpage lol
    console.log(data);
    })
    .catch((error) => console.error('Error:', error));

    
});    
  
