document.onreadystatechange = () => {
  if (document.readyState === 'interactive') {
    initApp();
  }
};

function initApp() {
  var createIdInput = document.querySelector('#createIdInput');
  var createIdBtn = document.querySelector('#createIdBtn');

  createIdInput.addEventListener('keyup', function() {
   var inputValue = this.value;

    if (inputValue === '') {
      createIdBtn.disabled = true;
    } else {
      createIdBtn.disabled = false;
    }
  })
}
