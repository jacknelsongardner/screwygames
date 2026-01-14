document.addEventListener("DOMContentLoaded", () => {
  const carousel = document.querySelector("[data-landingsite-carousel]");
  if (!carousel) return;

  const items = carousel.querySelectorAll("[data-landingsite-carousel-item]");
  const btnPrev = document.querySelector("[data-landingsite-carousel-controls-left]");
  const btnNext = document.querySelector("[data-landingsite-carousel-controls-right]");
  const indicatorsContainer = document.querySelector(
    "[data-landingsite-carousel-controls-index]"
  );

  let currentIndex = 0;
  const totalItems = items.length;

  function updateCarousel(index) {
    carousel.style.transform = `translateX(-${index * 100}%)`;

    if (indicatorsContainer) {
      [...indicatorsContainer.children].forEach((dot, i) => {
        dot.style.backgroundColor =
          i === index
            ? "var(--primary-color)"
            : "#C9CECD";
      });
    }
  }

  function goNext() {
    currentIndex = (currentIndex + 1) % totalItems;
    updateCarousel(currentIndex);
  }

  function goPrev() {
    currentIndex =
      (currentIndex - 1 + totalItems) % totalItems;
    updateCarousel(currentIndex);
  }

  // Button controls
  btnNext?.addEventListener("click", goNext);
  btnPrev?.addEventListener("click", goPrev);

  // Indicator controls
  if (indicatorsContainer) {
    [...indicatorsContainer.children].forEach((dot, index) => {
      dot.addEventListener("click", () => {
        currentIndex = index;
        updateCarousel(currentIndex);
      });
    });
  }

  // Optional: swipe support for touch devices
  let startX = 0;

  carousel.addEventListener("touchstart", (e) => {
    startX = e.touches[0].clientX;
  });

  carousel.addEventListener("touchend", (e) => {
    const endX = e.changedTouches[0].clientX;
    const diff = startX - endX;

    if (Math.abs(diff) > 50) {
      diff > 0 ? goNext() : goPrev();
    }
  });
});
