const express = require("express");
const app = express();

function authMiddleware(req, res, next) {
  next();
}
function getUsers(req, res) {
  res.send("Users");
}

app.get("/users", authMiddleware, getUsers);
app.post("/users", getUsers);
