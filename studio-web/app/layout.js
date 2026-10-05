export const metadata = { title: "Content Studio", description: "Create content with the Meta Model API" };
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
