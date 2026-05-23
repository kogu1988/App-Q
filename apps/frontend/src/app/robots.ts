import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        // Dashboard ve admin paneli — gizli, indexlenmemeli
        disallow: ["/admin/", "/client/", "/api/"],
      },
    ],
    sitemap: "https://clarere.com/sitemap.xml",
  };
}
