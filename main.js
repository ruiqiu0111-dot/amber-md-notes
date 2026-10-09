/* ===== Sidebar Toggle (Mobile) ===== */
const menuBtn = document.querySelector('.menu-toggle');
const sidebar = document.querySelector('.sidebar');
menuBtn.addEventListener('click', () => sidebar.classList.toggle('open'));

/* ===== Nav Group Collapse ===== */
function toggleNav(el) {
  el.classList.toggle('collapsed');
  const items = el.nextElementSibling;
  if (items && items.classList.contains('nav-items')) {
    items.classList.toggle('collapsed');
  }
}

/* ===== Bind click events ===== */
document.querySelectorAll('.nav-group').forEach(group => {
  group.addEventListener('click', function() {
    toggleNav(this);
  });
});

/* ===== QMMM Sub-items Toggle ===== */
const qmmmToggle = document.querySelector('.qmmm-toggle');
const qmmmSubItems = document.querySelector('.qmmm-sub-items');
const qmmmArrow = document.querySelector('.qmmm-arrow');
let qmmmExpanded = false;

if (qmmmToggle) {
  qmmmToggle.addEventListener('click', function(e) {
    e.preventDefault();
    qmmmExpanded = !qmmmExpanded;
    if (qmmmExpanded) {
      qmmmSubItems.style.maxHeight = qmmmSubItems.scrollHeight + 'px';
      qmmmArrow.style.transform = 'rotate(0deg)';
    } else {
      qmmmSubItems.style.maxHeight = '0px';
      qmmmArrow.style.transform = 'rotate(-90deg)';
    }
  });
}

/* ===== SMD Sub-items Toggle ===== */
const smdToggle = document.querySelector('.smd-toggle');
const smdSubItems = document.querySelector('.smd-sub-items');
const smdArrow = document.querySelector('.smd-arrow');
let smdExpanded = false;

if (smdToggle) {
  smdToggle.addEventListener('click', function(e) {
    e.preventDefault();
    smdExpanded = !smdExpanded;
    if (smdExpanded) {
      smdSubItems.style.maxHeight = smdSubItems.scrollHeight + 'px';
      smdArrow.style.transform = 'rotate(0deg)';
    } else {
      smdSubItems.style.maxHeight = '0px';
      smdArrow.style.transform = 'rotate(-90deg)';
    }
  });
}

/* ===== LiGaMD Sub-items Toggle ===== */
const ligamdToggle = document.querySelector('.ligamd-toggle');
const ligamdSubItems = document.querySelector('.ligamd-sub-items');
const ligamdArrow = document.querySelector('.ligamd-arrow');
let ligamdExpanded = false;

if (ligamdToggle) {
  ligamdToggle.addEventListener('click', function(e) {
    e.preventDefault();
    ligamdExpanded = !ligamdExpanded;
    if (ligamdExpanded) {
      ligamdSubItems.style.maxHeight = ligamdSubItems.scrollHeight + 'px';
      ligamdArrow.style.transform = 'rotate(0deg)';
    } else {
      ligamdSubItems.style.maxHeight = '0px';
      ligamdArrow.style.transform = 'rotate(-90deg)';
    }
  });
}

/* ===== Active Link on Scroll ===== */
const sections = document.querySelectorAll('.section[id]');
const navLinks = document.querySelectorAll('.sidebar a[href^="#"]');

function activateLink() {
  let current = '';
  sections.forEach(sec => {
    const top = sec.offsetTop - 100;
    if (scrollY >= top) current = sec.getAttribute('id');
  });
  navLinks.forEach(a => {
    a.classList.remove('active');
    if (a.getAttribute('href') === '#' + current) a.classList.add('active');
  });
}
window.addEventListener('scroll', activateLink);
activateLink();

/* ===== Close sidebar on link click (mobile) ===== */
navLinks.forEach(a => a.addEventListener('click', () => {
  if (window.innerWidth <= 860) sidebar.classList.remove('open');
}));

/* ===== Copy Code Button ===== */
document.querySelectorAll('.copy-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const code = btn.closest('.code-block').querySelector('pre').textContent;
    navigator.clipboard.writeText(code).then(() => {
      btn.textContent = '已复制';
      btn.classList.add('copied');
      setTimeout(() => { btn.textContent = '复制'; btn.classList.remove('copied'); }, 2000);
    });
  });
});

/* ===== Back to Top ===== */
const backBtn = document.querySelector('.back-top');
window.addEventListener('scroll', () => {
  backBtn.classList.toggle('show', scrollY > 400);
});
backBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

/* ===== Multiwfn Sub-items Toggle ===== */
const multiwfnToggle = document.querySelector('.multiwfn-toggle');
const multiwfnSubItems = document.querySelector('.multiwfn-sub-items');
const multiwfnArrow = document.querySelector('.multiwfn-arrow');
let multiwfnExpanded = false;

if (multiwfnToggle) {
  multiwfnToggle.addEventListener('click', function(e) {
    e.preventDefault();
    multiwfnExpanded = !multiwfnExpanded;
    if (multiwfnExpanded) {
      multiwfnSubItems.style.maxHeight = multiwfnSubItems.scrollHeight + 'px';
      multiwfnArrow.style.transform = 'rotate(0deg)';
    } else {
      multiwfnSubItems.style.maxHeight = '0px';
      multiwfnArrow.style.transform = 'rotate(-90deg)';
    }
  });
}

/* ===== VMD Force Sub-items Toggle ===== */
const vmdforceToggle = document.querySelector('.vmdforce-toggle');
const vmdforceSubItems = document.querySelector('.vmdforce-sub-items');
const vmdforceArrow = document.querySelector('.vmdforce-arrow');
let vmdforceExpanded = false;

if (vmdforceToggle) {
  vmdforceToggle.addEventListener('click', function(e) {
    e.preventDefault();
    vmdforceExpanded = !vmdforceExpanded;
    if (vmdforceExpanded) {
      vmdforceSubItems.style.maxHeight = vmdforceSubItems.scrollHeight + 'px';
      vmdforceArrow.style.transform = 'rotate(0deg)';
    } else {
      vmdforceSubItems.style.maxHeight = '0px';
      vmdforceArrow.style.transform = 'rotate(-90deg)';
    }
  });
}

