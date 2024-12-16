function addOrderLine() {
    var orderLinesDiv = document.getElementById('order_lines');
    var newLineInput = document.createElement('input');
    newLineInput.type = 'text';
    newLineInput.name = 'order_line';
    newLineInput.placeholder = 'Order Line ' + (orderLinesDiv.getElementsByTagName('input').length + 1);
    orderLinesDiv.appendChild(newLineInput);
    orderLinesDiv.appendChild(document.createElement('br'));
}

$(document).ready(function () {
    var socket = io();
    var progressTimeout;
      function resetTimeout() {
        clearTimeout(progressTimeout);
        progressTimeout = setTimeout(function() {
          socket.close();
          console.log('Connection timed out. No progress received.');
        }, 8000); // 8 seconds timeout for demonstration, adjust as necessary
      }

    $('#uploadForm').on('submit', function (event) {
        event.preventDefault();

        var formData = new FormData(this);

        $.ajax({
            url: $(this).attr('action'),
            type: $(this).attr('method'),
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                if (response.error) {
                    alert(response.error);
                } else {
                    $('#progressBar').width('0%').text('0%');
                }
            }
        });
    });

    socket.on('progress', function (data) {
        var percent = Math.round((data.current / data.total) * 100);
        $('#progressBar').width(percent + '%').text(percent + '%');
        // resetTimeout();
    });
});