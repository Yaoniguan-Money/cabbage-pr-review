# Frontend known warnings retained

- Vitest/Vite：React Babel plugin 的 `esbuild` option 已弃用；`optimizeDeps.esbuildOptions` 应迁移到 `optimizeDeps.rolldownOptions`。
- React Router tests：v7 的 `startTransition` 与 relative splat resolution future-flag 警告。
- Production build：约 615 kB 与 1129 kB 的 minified chunks 超过 500 kB 警戒线，建议后续做 dynamic import/manualChunks。
- `npm ci` audit：6 vulnerabilities（4 moderate、2 high）。本轮未执行 `npm audit fix --force`，避免未经验证的破坏性升级。

这些警告不影响本轮 35/35 tests 与 build success，但它们仍是待处理工程债务。
