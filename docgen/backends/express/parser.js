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
  extractChainedRouteMetadata,
} = require("./utils");

function parseFile(filePath) {
  const code = fs.readFileSync(filePath, "utf-8");
  const ast = parser.parse(code, {
    sourceType: "module",
    plugins: ["jsx"],
    attachComment: true,
  });

  const routes = [];
  const processedChains = new Set(); // Track processed chains to avoid duplication

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
        // Walk up the chain to find all methods and the base route
        const chainMethods = [];
        let currentCall = path.node;
        let routePath = "<unknown>";
        let baseRouteCall = null;

        // Collect all methods in the chain
        while (currentCall && currentCall.type === "CallExpression") {
          if (
            currentCall.callee.type === "MemberExpression" &&
            [
              "get",
              "post",
              "put",
              "delete",
              "patch",
              "head",
              "options",
            ].includes(currentCall.callee.property.name)
          ) {
            chainMethods.unshift({
              method: currentCall.callee.property.name.toUpperCase(),
              node: currentCall,
              args: currentCall.arguments,
            });
          } else if (
            currentCall.callee.type === "MemberExpression" &&
            currentCall.callee.property.name === "route" &&
            (currentCall.callee.object.name === "router" ||
              currentCall.callee.object.name === "app")
          ) {
            const pathArg = currentCall.arguments[0];
            routePath = pathArg?.value || "<unknown>";
            baseRouteCall = currentCall;
            break;
          }
          currentCall = currentCall.callee.object;
        }

        if (
          routePath !== "<unknown>" &&
          baseRouteCall &&
          chainMethods.length > 0
        ) {
          // Create a unique key for this chain based on route path and location
          const chainKey = `${routePath}:${baseRouteCall.start}:${baseRouteCall.end}`;

          // Only process if we haven't seen this chain before
          if (!processedChains.has(chainKey)) {
            processedChains.add(chainKey);

            // Find the ExpressionStatement that contains this chain
            let expressionStatement = path.parent;
            while (
              expressionStatement &&
              expressionStatement.type !== "ExpressionStatement"
            ) {
              expressionStatement = expressionStatement.parent;
            }

            // Process each method in the chain
            chainMethods.forEach((methodInfo, index) => {
              const isFirstInChain = index === 0;
              const method = methodInfo.method;
              const args = methodInfo.args;
              const middlewares = args
                .slice(0, -1)
                .map((arg) => arg.name || "<anonymous>");

              // Get previous method for trailing comment access
              const previousMethodInChain =
                index > 0 ? chainMethods[index - 1].node : null;

              const { description, metadata } = extractChainedRouteMetadata(
                { node: methodInfo.node },
                isFirstInChain,
                expressionStatement || baseRouteCall,
                previousMethodInChain
              );

              const { normalized_path, extracted_params } =
                normalizeExpressPath(routePath);

              const originalParams = metadata.param || [];
              const nonPathParams = originalParams.filter(
                (p) => p.in !== "path"
              );
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
            });
          }
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
