import "./globals.css";

export const metadata = {
  title: "Zetta Lead Enrichment",
  description: "Company enrichment dashboard"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
