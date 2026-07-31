// ======================================
// Diamond Price Prediction Website
// ======================================

console.log("Website Loaded Successfully!");

const input=document.getElementById("searchInput");

if(input){

input.addEventListener("keyup",function(){

let filter=input.value.toLowerCase();

let rows=document.querySelectorAll("#historyTable tbody tr");

rows.forEach(function(row){

let text=row.innerText.toLowerCase();

row.style.display=text.includes(filter)?"":"none";

});

});

}