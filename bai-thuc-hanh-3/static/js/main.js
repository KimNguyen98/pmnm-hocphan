// Nút −/+ chỉnh số lượng ở trang chi tiết sách
document.querySelectorAll(".qty-group").forEach(function (group) {
  var input = group.querySelector("input");
  var max = parseInt(group.dataset.max, 10) || 1;
  group.querySelectorAll("[data-step]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var v = (parseInt(input.value, 10) || 1) + parseInt(btn.dataset.step, 10);
      input.value = Math.min(Math.max(v, 1), max);
    });
  });
});