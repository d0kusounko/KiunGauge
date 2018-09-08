$(function(){
    $('.settings_apply').on('click', function(e){
      e.preventDefault();  // Aタグによる画面遷移を無効.

      // フォームをPOST.
      var $form = $(document.getElementById('kiun_form'));
      $form.attr('action', $(this).attr('href') );
      $form.submit();
    });
});
