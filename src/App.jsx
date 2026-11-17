import React, { useEffect } from "react";
import { Router, useRouter } from "./router";
import HomePage from "./pages/HomePage";
import AboutPage from "./pages/AboutPage";
import ServicesPage from "./pages/ServicesPage";
import SolutionsPage from "./pages/SolutionsPage";
import PortfolioPage from "./pages/PortfolioPage";
import InsightsPage from "./pages/InsightsPage";
import ContactPage from "./pages/ContactPage";
import LandingPage from "./pages/LandingPage";

function PageRouter() {
  const { path } = useRouter();

  // Strip hash and search query before matching routes
  const cleanPath = (path || "/").split("#")[0].split("?")[0] || "/";
  const normalizedPath =
    cleanPath.length > 1 && cleanPath.endsWith("/")
      ? cleanPath.slice(0, -1)
      : cleanPath;

  // Dynamically update document title based on route for SEO and browser tabs
  useEffect(() => {
    const titles = {
      "/": "Ariyx Systems",
      "/about": "About | Ariyx Systems",
      "/services": "Services | Ariyx Systems",
      "/solutions": "Solutions | Ariyx Systems",
      "/portfolio": "Portfolio | Ariyx Systems",
      "/insights": "Insights | Ariyx Systems",
      "/contact": "Contact | Ariyx Systems",
      "/growth": "Ariyx Systems",
      "/scale": "Ariyx Systems",
    };
    document.title = titles[normalizedPath] || "Ariyx Systems";
  }, [normalizedPath]);

  switch (normalizedPath) {
    case "/":
      return <HomePage />;
    case "/about":
      return <AboutPage />;
    case "/services":
      return <ServicesPage />;
    case "/solutions":
      return <SolutionsPage />;
    case "/portfolio":
      return <PortfolioPage />;
    case "/insights":
      return <InsightsPage />;
    case "/contact":
      return <ContactPage />;
    case "/growth":
    case "/scale":
      return <LandingPage />;
    default:
      return <HomePage />;
  }
}

export default function App() {
  return (
    <Router>
      <PageRouter />
    </Router>
  );
}
