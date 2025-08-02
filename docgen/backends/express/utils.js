/**
 * Utilities for normalizing Express.js routes and extracting metadata.
 * Contains functions for path parameter normalization and comment parsing.
 */

function normalizeExpressPath(routePath) {
  // Pattern to match Express path parameters like :id, :userId, etc.
  const pattern = /:([a-zA-Z_][a-zA-Z0-9_]*)/g;

  const extractedParams = [];

  const normalizedPath = routePath.replace(pattern, (match, paramName) => {
    extractedParams.push({
      name: paramName,
      type: "string", // Express doesn't specify types, default to string
      in: "path",
      required: true, // Path parameters are always required
    });
    return `{${paramName}}`;
  });

  return {
    normalized_path: normalizedPath,
    extracted_params: extractedParams,
  };
}

function mergePathParamsWithMetadata(extractedParams, metadataParams) {
  const metadataLookup = {};
  for (const param of metadataParams) {
    if (param.in === "path") {
      metadataLookup[param.name] = param;
    }
  }

  const mergedParams = [];

  // Process extracted path parameters
  for (const extracted of extractedParams) {
    const paramName = extracted.name;
    if (paramName in metadataLookup) {
      // Merge with metadata, keeping type info from extraction but description from metadata
      const metadata = metadataLookup[paramName];
      const mergedParam = {
        name: paramName,
        type: extracted.type || metadata.type || "string",
        in: "path",
        required: true, // Path params are always required
        description: metadata.description || `${paramName} parameter`,
      };
      if (extracted.format) {
        mergedParam.format = extracted.format;
      }
      mergedParams.push(mergedParam);
      // Remove from metadata lookup so we don't duplicate
      delete metadataLookup[paramName];
    } else {
      // No metadata found, use extracted info with default description
      extracted.description = `${paramName} parameter`;
      mergedParams.push(extracted);
    }
  }

  // Add any remaining path parameters from metadata that weren't found in the path
  for (const remainingParam of Object.values(metadataLookup)) {
    mergedParams.push(remainingParam);
  }

  return mergedParams;
}

function parseParamTag(line) {
  const regex = /@param\s+{(\w+)}\s+(\w+)\.(\w+)(?:\.required)?\s*-\s*(.*)/;
  const match = line.match(regex);
  if (!match) return null;

  const [, type, name, location, description] = match;
  const required = line.includes(".required");

  return {
    name,
    in: location,
    type,
    required,
    description: description.trim(),
  };
}

function parseReturnsTag(line) {
  const regex = /@returns\s+{(\w+)}\s+(\d{3})\s*-\s*(.*)/;
  const match = line.match(regex);
  if (!match) return null;

  const [, type, statusCode, description] = match;

  return {
    type,
    statusCode: parseInt(statusCode),
    description: description.trim(),
  };
}

function extractCommentMetadata(path) {
  const comments = path.node.leadingComments || path.parent?.leadingComments;
  if (!comments || comments.length === 0)
    return { description: "", metadata: {} };

  const last = comments[comments.length - 1];
  const lines = last.value
    .split("\n")
    .map((line) => line.replace(/^\s*\*\s?/, "").trim())
    .filter((line) => line.length > 0);

  let descriptionLines = [];
  let metadata = {};

  for (const line of lines) {
    if (line.startsWith("@")) {
      const [tag, ...rest] = line.split(" ");
      const key = tag.slice(1).trim();
      const value = rest.join(" ").trim();

      if (key === "param") {
        const parsed = parseParamTag(line);
        if (parsed) {
          if (!metadata[key]) metadata[key] = [];
          metadata[key].push(parsed);
          continue;
        }
      }

      if (key === "returns") {
        const parsed = parseReturnsTag(line);
        if (parsed) {
          if (!metadata[key]) metadata[key] = [];
          metadata[key].push(parsed);
          continue;
        }
      }

      if (metadata[key]) {
        if (Array.isArray(metadata[key])) {
          metadata[key].push(value);
        } else {
          metadata[key] = [metadata[key], value];
        }
      } else {
        metadata[key] = value;
      }
    } else {
      descriptionLines.push(line);
    }
  }

  return {
    description: descriptionLines.join(" "),
    metadata,
  };
}

module.exports = {
  normalizeExpressPath,
  mergePathParamsWithMetadata,
  parseParamTag,
  parseReturnsTag,
  extractCommentMetadata,
};
