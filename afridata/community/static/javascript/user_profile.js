document.addEventListener('DOMContentLoaded', function() {
        // Initialize Bootstrap tabs
        var triggerTabList = [].slice.call(document.querySelectorAll('#activity-tabs button'));
        triggerTabList.forEach(function (triggerEl) {
            var tabTrigger = new bootstrap.Tab(triggerEl);
            
            triggerEl.addEventListener('click', function (event) {
                event.preventDefault();
                tabTrigger.show();
            });
        });
        
        // Smooth scroll to tabs when clicking
        document.querySelectorAll('#activity-tabs button').forEach(function(tab) {
            tab.addEventListener('shown.bs.tab', function() {
                const tabContent = document.querySelector('.tab-content');
                if (tabContent) {
                    tabContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
        
        // Add loading animation to activity items
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animationPlayState = 'running';
                }
            });
        }, observerOptions);
        
        // Observe all activity items
        document.querySelectorAll('.activity-item').forEach(item => {
            item.style.animationPlayState = 'paused';
            observer.observe(item);
        });
        
        // Add hover effects for cards
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
        
        // Add click animation for buttons
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', function(e) {
                let ripple = document.createElement('span');
                ripple.classList.add('ripple');
                this.appendChild(ripple);
                
                let x = e.clientX - e.target.offsetLeft;
                let y = e.clientY - e.target.offsetTop;
                
                ripple.style.left = `${x}px`;
                ripple.style.top = `${y}px`;
                
                setTimeout(() => {
                    ripple.remove();
                }, 600);
            });
        });
        
        // Animate achievement badges on hover
        document.querySelectorAll('.achievement-badge').forEach(badge => {
            badge.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.1) rotate(2deg)';
            });
            
            badge.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1) rotate(0deg)';
            });
        });
        
        // Add parallax effect to profile avatar
        document.addEventListener('mousemove', function(e) {
            const avatar = document.querySelector('.profile-avatar, .profile-avatar-placeholder');
            if (avatar) {
                const rect = avatar.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                
                const moveX = x * 0.01;
                const moveY = y * 0.01;
                
                avatar.style.transform = `translate(${moveX}px, ${moveY}px) scale(1.02)`;
            }
        });
        
        // Reset avatar position when mouse leaves
        document.addEventListener('mouseleave', function() {
            const avatar = document.querySelector('.profile-avatar, .profile-avatar-placeholder');
            if (avatar) {
                avatar.style.transform = 'translate(0px, 0px) scale(1)';
            }
        });
        
        // Add typing effect for empty state messages
        function typeWriter(element, text, speed = 50) {
            let i = 0;
            element.innerHTML = '';
            
            function type() {
                if (i < text.length) {
                    element.innerHTML += text.charAt(i);
                    i++;
                    setTimeout(type, speed);
                }
            }
            type();
        }
        
        // Apply typing effect to empty state messages
        const emptyMessages = document.querySelectorAll('.empty-state p');
        emptyMessages.forEach((msg, index) => {
            const originalText = msg.textContent;
            setTimeout(() => {
                typeWriter(msg, originalText, 30);
            }, index * 1000);
        });
        
        // Add smooth reveal animation for stats
        function animateValue(element, start, end, duration) {
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                const current = Math.floor(progress * (end - start) + start);
                element.innerHTML = current;
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                }
            };
            window.requestAnimationFrame(step);
        }
        
        // Animate stat numbers when they come into view
        const statNumbers = document.querySelectorAll('.stat-number');
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = entry.target;
                    const finalValue = parseInt(target.textContent);
                    animateValue(target, 0, finalValue, 1500);
                    statsObserver.unobserve(target);
                }
            });
        });
        
        statNumbers.forEach(stat => {
            statsObserver.observe(stat);
        });
    });