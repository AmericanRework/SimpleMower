const http = require('http');
const fs = require('fs');

//start this one for toby web remote!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

//type in node MyTobyServer.js to run this.
//then go to the IP addresss. 

//writes key press to /dev/shm 'cause that's in memory so we don't hammer the flash with 1 write per second and wreck it.



const server = http.createServer((req, res) => {
  if (req.url === '/') {
    fs.readFile('index.html', (err, data) => {
      if (err) {
        res.statusCode = 500;
        res.end(`Error: ${err}`);
      } else {
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(data);
      }
    });
  } else if (req.url === '/script.js') {
    fs.readFile('script.js', (err, data) => {
      if (err) {
        res.statusCode = 500;
        res.end(`Error: ${err}`);
      } else {
        res.end(data);
      }
    });
  } else if (req.method === 'POST' && req.url === '/writefile') {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk;
      // todo? also include a timestamp here - then can store a 'last pressed time'
    });
    req.on('end', () => {
      fs.writeFile('/dev/shm/KeyCommands.txt', body, (err) => {
        if (err) throw err;
      });


      console.log('File has been written');
      
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.write('Instruction sent!');
      fs.readFile('/dev/shm/RobotStatus.txt', (err, data) => {
      if (err) {
        res.statusCode = 500;
        res.end(`Error: ${err}`);
      } else {
        res.end(data);
      }});
     // res.end('Holy moly javasript.... ');
    });
  }
});

server.listen(8001, '0.0.0.0', () => {
  console.log('Server is running on port 8001');
});