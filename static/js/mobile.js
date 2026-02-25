// Mobile Navigation and Interactivity for Liesbeek Management System

document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            mobileMenu.classList.toggle('hidden');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenu.contains(e.target) && !menuToggle.contains(e.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
    }
    
    // Hide mobile nav on scroll down, show on scroll up
    let lastScroll = 0;
    const mobileNav = document.querySelector('.mobile-nav');
    
    if (mobileNav) {
        window.addEventListener('scroll', function() {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll > lastScroll && currentScroll > 100) {
                mobileNav.style.transform = 'translateY(100%)';
            } else {
                mobileNav.style.transform = 'translateY(0)';
            }
            
            lastScroll = currentScroll;
        }, { passive: true });
    }
    
    // Enhance counter buttons for touch feedback
    document.querySelectorAll('.counter-btn').forEach(btn => {
        btn.addEventListener('touchstart', function() {
            this.classList.add('active');
        });
        btn.addEventListener('touchend', function() {
            this.classList.remove('active');
        });
    });
    
    // Floating action button visibility
    const fab = document.getElementById('mobile-add-log-btn');
    if (fab) {
        // Show/hide FAB based on scroll
        let fabLastScroll = 0;
        window.addEventListener('scroll', function() {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll > fabLastScroll && currentScroll > 200) {
                fab.style.transform = 'translateY(100px)';
                fab.style.opacity = '0';
            } else {
                fab.style.transform = 'translateY(0)';
                fab.style.opacity = '1';
            }
            
            fabLastScroll = currentScroll;
        }, { passive: true });
    }
    
    // Section toggle for mobile - ensure proper tap targets
    document.querySelectorAll('.section-header').forEach(header => {
        header.addEventListener('click', function(e) {
            // Visual feedback
            this.style.backgroundColor = 'rgba(0,0,0,0.05)';
            setTimeout(() => {
                this.style.backgroundColor = '';
            }, 150);
        });
    });
    
    // Prevent zoom on input focus for iOS
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                document.body.style.zoom = '1';
            });
        });
    }
});

// Utility function to detect touch devices
function isTouchDevice() {
    return (('ontouchstart' in window) ||
        (navigator.maxTouchPoints > 0) ||
        (navigator.msMaxTouchPoints > 0));
}

// Add touch-specific classes to body
if (isTouchDevice()) {
    document.body.classList.add('touch-device');
}

// Handle form submissions with loading state
function handleMobileFormSubmit(form) {
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span> Saving...';
    }
}

// Photo upload preview for mobile
function previewMobilePhoto(input) {
    const preview = document.getElementById('photoPreview');
    const placeholder = document.getElementById('uploadPlaceholder');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (preview) {
                preview.src = e.target.result;
                preview.classList.remove('hidden');
            }
            if (placeholder) {
                placeholder.classList.add('hidden');
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}
