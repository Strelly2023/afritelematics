const path = require("path");
const { getDefaultConfig } = require("expo/metro-config");

const projectRoot = __dirname;
const sharedRoot = path.resolve(projectRoot, "../afriride_system/mobile/shared");
const config = getDefaultConfig(projectRoot);
config.watchFolders = [...(config.watchFolders || []), sharedRoot];
config.resolver.nodeModulesPaths = [path.resolve(projectRoot, "node_modules")];

module.exports = config;
