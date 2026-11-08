import React, { createContext, useContext, useState, useEffect } from "react";

const RouterContext = createContext({
  path: "/",
  navigate: () => {},
});

export function Router({ children }) {
  const [path, setPath] = useState(
    (window.location.pathname || "/") + (window.location.hash || "")
  );

  const scrollToHash = (hash) => {
    if (!hash) return;
    setTimeout(() => {
      try {
        const el = document.querySelector(hash);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      } catch (_) {}
    }, 80);
  };

  useEffect(() => {
    const handlePopState = () => {
      const fullPath =
        (window.location.pathname || "/") + (window.location.hash || "");
      setPath(fullPath);
      if (window.location.hash) {
        scrollToHash(window.location.hash);
      }
    };

    window.addEventListener("popstate", handlePopState);

    // Initial load scroll if hash exists in URL
    if (window.location.hash) {
      scrollToHash(window.location.hash);
    }

    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = (to) => {
    if (!to) return;

    // Handle hash anchors on the same page or external routes
    const [targetPath, hash] = to.split("#");
    const targetPathname = targetPath || window.location.pathname;
    const targetHash = hash ? `#${hash}` : "";
    const fullTarget = targetPathname + targetHash;

    const currentPathname = window.location.pathname;

    if (targetPathname === currentPathname) {
      if (targetHash) {
        window.history.pushState({}, "", fullTarget);
        setPath(fullTarget);
        scrollToHash(targetHash);
      } else {
        window.history.pushState({}, "", fullTarget);
        setPath(fullTarget);
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
      return;
    }

    window.history.pushState({}, "", fullTarget);
    setPath(fullTarget);

    if (targetHash) {
      scrollToHash(targetHash);
    } else {
      window.scrollTo({ top: 0, behavior: "instant" });
    }
  };

  return (
    <RouterContext.Provider value={{ path, navigate }}>
      {children}
    </RouterContext.Provider>
  );
}

export function useRouter() {
  return useContext(RouterContext);
}

export function Link({ to, children, className = "", onClick, ...props }) {
  const { navigate } = useRouter();

  const handleClick = (e) => {
    if (onClick) onClick(e);
    if (e.defaultPrevented) return;

    // If external or modifier keys pressed, let browser handle naturally
    if (
      to.startsWith("http://") ||
      to.startsWith("https://") ||
      to.startsWith("mailto:") ||
      to.startsWith("tel:") ||
      e.metaKey ||
      e.ctrlKey ||
      e.shiftKey ||
      e.altKey
    ) {
      return;
    }

    e.preventDefault();
    navigate(to);
  };

  return (
    <a href={to} onClick={handleClick} className={className} {...props}>
      {children}
    </a>
  );
}
