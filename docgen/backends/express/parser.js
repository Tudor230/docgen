const fs = require("fs");
const path = require("path");
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const {
  normalizeExpressPath,
  mergePathParamsWithMetadata,
  parseParamTag,
  parseReturnsTag,
  extractCommentMetadata,
} = require("./utils");

const HTTP_METHODS = [
  "get",
  "post",
  "put",
  "delete",
  "patch",
  "head",
  "options",
];

function isHttpMethod(name) {
  return HTTP_METHODS.includes(name);
}

/** Pick the correct leading comment block for a method call. */
function getCommentNodes({ methodPath, isFirstMethod, baseRoutePath }) {
  // 1. Own leading comments
  if (methodPath.node.leadingComments?.length)
    return methodPath.node.leadingComments;
  // 2. Leading comments of the handler function (last arg) – covers
  //      router.get("/x",
  //      /** docs */ (req,res)=>{})
  const lastArg = methodPath.get("arguments").pop();
  if (lastArg?.node?.leadingComments?.length)
    return lastArg.node.leadingComments;
  // 3. Leading comments of router.route("/x") – only for the *first* method
  if (isFirstMethod && baseRoutePath.node.leadingComments?.length)
    return baseRoutePath.node.leadingComments;
  // Nothing found
  return [];
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

        const { description, metadata } = extractCommentMetadata(path);

        // Normalize path parameters
        const { normalized_path, extracted_params } =
          normalizeExpressPath(routePath);

        // Merge extracted path params with metadata params
        const originalParams = metadata.param || [];
        const nonPathParams = originalParams.filter((p) => p.in !== "path");
        const mergedPathParams = mergePathParamsWithMetadata(
          extracted_params,
          originalParams
        );
        const allParams = [...mergedPathParams, ...nonPathParams];

        // Update metadata with merged parameters
        const updatedMetadata = { ...metadata };
        if (allParams.length > 0) {
          updatedMetadata.param = allParams;
        }

        routes.push({
          method,
          path: normalized_path,
          description: description || "",
          middlewares,
          metadata: updatedMetadata,
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

          const { description, metadata } = extractCommentMetadata(path);
          const { normalized_path, extracted_params } =
            normalizeExpressPath(routePath);

          const originalParams = metadata.param || [];
          const nonPathParams = originalParams.filter((p) => p.in !== "path");
          const mergedPathParams = mergePathParamsWithMetadata(
            extracted_params,
            originalParams
          );
          const allParams = [...mergedPathParams, ...nonPathParams];

          const updatedMetadata = { ...metadata };
          if (allParams.length > 0) {
            updatedMetadata.param = allParams;
          }

          routes.push({
            method,
            path: normalized_path,
            description: description || "",
            middlewares,
            metadata: updatedMetadata,
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
