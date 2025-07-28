const fs = require("fs");
const path = require("path");
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;

function extractDescription(path) {
  const parentComments = path.parent && path.parent.leadingComments;

  const comments = parentComments;
  if (!comments || comments.length === 0) return "";

  const comment = comments[comments.length - 1];
  if (!comment || !comment.value) return "";

  const value = comment.value;

  return value
    .split("\n")
    .map((line) => line.replace(/^\s*\*\s?/, "").trim())
    .filter((line) => line.length > 0)
    .join(" ")
    .trim();
}

function parseFile(filePath) {
  const code = fs.readFileSync(filePath, "utf-8");
  const ast = parser.parse(code, {
    sourceType: "module",
    plugins: ["jsx"],
    attachComment: true,
  });

  const routes = [];

  traverse(ast, {
    CallExpression(path) {
      const callee = path.node.callee;

      // Handle basic routes like app.get(), router.post(), etc.
      if (
        callee.type === "MemberExpression" &&
        (callee.object.name === "app" || callee.object.name === "router") &&
        ["get", "post", "put", "delete", "patch", "head", "options"].includes(
          callee.property.name
        )
      ) {
        const method = callee.property.name.toUpperCase();
        const args = path.node.arguments;

        const routePath = args[0].value;
        const middlewares = args
          .slice(1, -1)
          .map((arg) => arg.name || "<anonymous>");

        const description = extractDescription(path);

        routes.push({
          method,
          path: routePath,
          description: description || "",
          middlewares,
        });
      }

      // Handle chained routes like router.route("/path").get().post()
      if (
        callee.type === "MemberExpression" &&
        callee.object.type === "CallExpression" &&
        ["get", "post", "put", "delete", "patch", "head", "options"].includes(
          callee.property.name
        )
      ) {
        // Walk up the chain to find the route call
        let current = callee.object;
        let routePath = "<unknown>";

        while (current && current.type === "CallExpression") {
          if (
            current.callee.type === "MemberExpression" &&
            current.callee.property.name === "route" &&
            (current.callee.object.name === "router" ||
              current.callee.object.name === "app")
          ) {
            const pathArg = current.arguments[0];
            routePath = pathArg?.value || "<unknown>";
            break;
          }
          current = current.callee.object;
        }

        if (routePath !== "<unknown>") {
          const method = callee.property.name.toUpperCase();
          const args = path.node.arguments;
          const middlewares = args
            .slice(0, -1)
            .map((arg) => arg.name || "<anonymous>");

          const description = extractDescription(path);

          routes.push({
            method,
            path: routePath,
            description: description || "",
            middlewares,
          });
        }
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
