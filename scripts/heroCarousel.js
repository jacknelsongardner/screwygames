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

  var AUTO_DELAY = 4500;
  let autoTimer = null;

  function updateCarousel(index) {
    carousel.style.transform = `translateX(-${index * 100}%)`;

    if (indicatorsContainer) {
      [...indicatorsContainer.children].forEach((dot, i) => {
        dot.style.backgroundColor =
          i === index ? "var(--primary-color)" : "#C9CECD";
      });
    }
  }

  function goNext(delay=4500) {
    AUTO_DELAY = delay;
    currentIndex = (currentIndex + 1) % totalItems;
    updateCarousel(currentIndex);
    resetAuto();
  }

  function goPrev(delay=4500) {
    AUTO_DELAY = delay;
    currentIndex = (currentIndex - 1 + totalItems) % totalItems;
    updateCarousel(currentIndex);
    resetAuto();
  }

  function startAuto() {
    autoTimer = setInterval(goNext, AUTO_DELAY);
  }

  function resetAuto() {
    clearInterval(autoTimer);
    startAuto();
  }

  // Button controls
  btnNext?.addEventListener("click", () => goNext(9000));
  btnPrev?.addEventListener("click", () => goPrev(9000));

  // Indicator controls
  if (indicatorsContainer) {
    [...indicatorsContainer.children].forEach((dot, index) => {
      dot.addEventListener("click", () => {
        currentIndex = index;
        updateCarousel(currentIndex);
        resetAuto();
      });
    });
  }

  // Swipe support
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

  // Start autoplay
  startAuto();
});
