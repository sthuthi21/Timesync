document.addEventListener("DOMContentLoaded", () => {
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    let currentMonth = 2; // March (Index 2)
    let currentYear = 2025;

    const calendarTitle = document.querySelector(".calendar h2");
    const calendarTable = document.querySelector("#calendarTable");
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

    function updateSchedule(selectedDay) {
        document.querySelector(".schedule h2").textContent = `${monthNames[currentMonth]} ${selectedDay}, ${currentYear}`;
    }

    // **Ensure the calendar is generated as soon as the page loads**
    updateCalendar();
});
