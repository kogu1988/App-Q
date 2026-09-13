import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  // React 19'un yeni danışma (advisory) kuralı: setState'i effect içinde çağırma.
  // Bilinçli kullanımlar var (hydration guard + grounded form türetmesi); hata
  // değil performans uyarısıdır → uyarı seviyesinde tutulur, CI'yı düşürmez.
  {
    rules: {
      "react-hooks/set-state-in-effect": "warn",
    },
  },
]);

export default eslintConfig;
