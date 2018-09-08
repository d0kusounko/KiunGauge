$(function(){
  {% if twitter_login == True %}

    {% for kiun_name in kiun_names %}
      var gauge{{ loop.index0 }} = document.getElementById('kiungauge{{ loop.index0 }}');
      if( gauge{{ loop.index0 }} )
      {
        // ボタンクリックで機運上げ.
        $('#plus_button{{ loop.index0 }}').click(function(e) {
          gauge{{ loop.index0 }}.value = gauge{{ loop.index0 }}.value + 1;
        });
        // ボタンクリックで機運下げ.
        $('#minus_button{{ loop.index0 }}').click(function(e) {
          gauge{{ loop.index0 }}.value = gauge{{ loop.index0 }}.value - 1;
        });
      }
    {% endfor %}

    // 機運更新.
    $(".kiun_update").on('click',function(e){
        e.preventDefault();   // Aタグによる画面遷移を無効.

        var data = {};
        data['values'] = [];
        {% for kiun_value in kiun_values %}

         if( gauge{{ loop.index0 }} )
         {
            data['values'].push( gauge{{ loop.index0 }}.value );
         }
         else
         {
            data['values'].push(0);
         }

        {% endfor %}

        url = $(this).attr('href')

        var $form = $('<form/>', {'action': url, 'method': 'post'});

        for(var key in data) {
          if( Array.isArray( data[key] ) == true )
          {
            for( var i in data[key] )
            {
              $form.append($('<input/>', {'type': 'hidden', 'name': key, 'value': data[key][i]}));
            }
          }
          else
          {
            $form.append($('<input/>', {'type': 'hidden', 'name': key, 'value': data[key]}));
          }
        }

        $form.appendTo(document.body);
        $form.submit();
    });

  {% endif %}

});
