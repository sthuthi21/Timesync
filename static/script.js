const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
let currentMonth = 2; // March (Index 2)
let currentYear = 2025;


const calendarTitle = document.querySelector(".calendar h2");
const calendarTable = document.querySelector("table");
const prevBtn = document.querySelectorAll(".nav-btn")[0];
const nextBtn = document.querySelectorAll(".nav-btn")[1];


function updateCalendar() {
    calendarTitle.textContent = `${monthNames[currentMonth]} ${currentYear}`;
   
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();


    let html = "<tr><th>Su</th> <th>Mo</th> <th>Tu</th> <th>We</th> <th>Th</th> <th>Fr</th> <th>Sa</th></tr><tr>";


    for (let i = 0; i < firstDay; i++) {
        html += "<td></td>";
    }


    for (let day = 1; day <= daysInMonth; day++) {
        if ((firstDay + day - 1) % 7 === 0 && day !== 1) {
            html += "</tr><tr>";
        }
        html += `<td class="day">${day}</td>`;
    }


    html += "</tr>";
    calendarTable.innerHTML = html;


    // Add event listeners for selecting a day
    document.querySelectorAll(".day").forEach(dayElement => {
        dayElement.addEventListener("click", () => {
            document.querySelectorAll(".day").forEach(d => d.classList.remove("selected"));
            dayElement.classList.add("selected");
            updateSchedule(parseInt(dayElement.textContent));
        });
    });
}

/*async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });
    const data = await response.json();
    if (response.ok) {
        localStorage.setItem("token", data.token);  // Store token for future requests
        window.location.href = "dashboard.html";
    } else {
        alert(data.error);
    }
}*/

prevBtn.addEventListener("click", () => {
    currentMonth--;
    if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    }
    updateCalendar();
});


nextBtn.addEventListener("click", () => {
    currentMonth++;
    if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    }
    updateCalendar();
});

document.getElementById("generate-btn").addEventListener("click", async () => {
    const startTime = document.querySelector("#start-time").value;
    const endTime = document.querySelector("#end-time").value;
    const breakInterval = document.querySelector("#break-interval").value;
    const breakDuration = document.querySelector("#break-duration").value;
    
    // Get tasks
    const tasks = []; // Populate with user-entered tasks

    const response = await fetch("http://localhost:5000/generate-timetable", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            start_time: startTime,
            end_time: endTime,
            tasks: tasks,
            break_interval: breakInterval,
            break_duration: breakDuration
        }),
    });

    const schedule = await response.json();
    console.log(schedule); // Update UI with the generated schedule
});


function updateSchedule(selectedDay) {
    document.querySelector(".schedule h2").textContent = `${monthNames[currentMonth]} ${selectedDay}, ${currentYear}`;
}

//login();
updateCalendar();


