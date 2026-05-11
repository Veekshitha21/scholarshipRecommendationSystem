// Welcome Page Animation Script

document.addEventListener('DOMContentLoaded', () => {
  initAnimations();
  animateCounters();
});

function initAnimations() {
  // Observe elements for scroll animations
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  });

  // Observe step cards and feature items
  document.querySelectorAll('.step-card, .feature-item, .stat-card').forEach((el) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
    observer.observe(el);
  });
}

function animateCounters() {
  const counterElements = document.querySelectorAll('.stat-number');
  const observerOptions = {
    threshold: 0.5
  };

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && !entry.target.dataset.counted) {
        entry.target.dataset.counted = 'true';
        const target = parseInt(entry.target.dataset.target, 10);
        animateValue(entry.target, 0, target, 2000);
      }
    });
  }, observerOptions);

  counterElements.forEach((el) => {
    counterObserver.observe(el);
  });
}

function animateValue(element, start, end, duration) {
  let startTimestamp = null;
  
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const value = Math.floor(progress * (end - start) + start);
    
    // Format large numbers with commas
    if (end > 1000) {
      element.textContent = value.toLocaleString();
    } else {
      element.textContent = value + (element.dataset.target.includes('.') ? '%' : '');
    }
    
    if (progress < 1) {
      requestAnimationFrame(step);
    }
  };
  
  requestAnimationFrame(step);
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// Add parallax effect to blobs on scroll
window.addEventListener('scroll', () => {
  const scrollPosition = window.scrollY;
  const blobs = document.querySelectorAll('.gradient-blob');
  
  blobs.forEach((blob, index) => {
    blob.style.transform = `translateY(${scrollPosition * 0.1 * (index + 1)}px)`;
  });
});

// Add hover effects to buttons
document.querySelectorAll('.btn-cta').forEach((button) => {
  button.addEventListener('mouseenter', function () {
    this.style.transform = 'translateY(-4px)';
  });

  button.addEventListener('mouseleave', function () {
    this.style.transform = 'translateY(0)';
  });
});

console.log('Welcome page animations initialized');
