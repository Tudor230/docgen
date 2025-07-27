const fs = require("fs");
const path = require("path");
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;

function parseFile(filePath) {
  const code = fs.readFileSync(filePath, "utf-8");
  const ast = parser.parse(code, {
    sourceType: "module",
    plugins: ["jsx"],
  });

  const routes = [];

  traverse(ast, {
    CallExpression(path) {
      const callee = path.node.callee;

      if (
        callee.type === "MemberExpression" &&
        (callee.object.name === "app" || callee.object.name === "router") &&
        ["get", "post", "put", "delete"].includes(callee.property.name)
      ) {
        const method = callee.property.name.toUpperCase();
        const args = path.node.arguments;

        const routePath = args[0].value;
        const middlewares = args
          .slice(1, -1)
          .map((arg) => arg.name || "<anonymous>");

        routes.push({
          method,
          path: routePath,
          description: "", // Optional: extract from comments later
          middlewares,
        });
      }
    },
  });

  return routes;
}

function getAllJSFiles(dirPath, fileList = []) {
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.resolve(dirPath, entry.name);
    if (entry.isDirectory()) {
      getAllJSFiles(fullPath, fileList);
    } else if (entry.isFile() && fullPath.endsWith(".js")) {
      fileList.push(fullPath);
    }
  }

  return fileList;
}

const inputDir = process.argv[2];
const files = getAllJSFiles(inputDir);
let allRoutes = [];

for (const file of files) {
  allRoutes = allRoutes.concat(parseFile(file));
}

console.log(JSON.stringify(allRoutes, null, 2));
