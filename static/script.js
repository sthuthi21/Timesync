document.addEventListener("DOMContentLoaded", () => {
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const today = new Date();
    currentYear = today.getFullYear();
    currentMonth = today.getMonth();
    const currentDay = today.getDate();

    const calendarTitle = document.querySelector(".calendar h2");
    const calendarTable = document.querySelector("#calendarTable");
    const prevBtn = document.querySelectorAll(".nav-btn")[0];
    const nextBtn = document.querySelectorAll(".nav-btn")[1];

    function updateCalendar() {
        calendarTitle.textContent = `${monthNames[currentMonth]} ${currentYear}`;
    
        const firstDay = new Date(currentYear, currentMonth, 1).getDay();
        const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
        const today = new Date();
        const isCurrentMonth = today.getFullYear() === currentYear && today.getMonth() === currentMonth;
        const currentDay = isCurrentMonth ? today.getDate() : null; // Check if today is in the displayed month
    
        let html = "<tr><th>Su</th> <th>Mo</th> <th>Tu</th> <th>We</th> <th>Th</th> <th>Fr</th> <th>Sa</th></tr><tr>";
    
        for (let i = 0; i < firstDay; i++) {
            html += "<td></td>";
        }
    
        for (let day = 1; day <= daysInMonth; day++) {
            const isToday = day === currentDay;
            html += `<td class="day ${isToday ? 'selected' : ''}">${day}</td>`;
    
            if ((firstDay + day) % 7 === 0) {
                html += "</tr><tr>";
            }
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

    async function updateSchedule(selectedDay) {
        const formattedDate = `${currentYear}-${(currentMonth + 1).toString().padStart(2, "0")}-${selectedDay.toString().padStart(2, "0")}`;
        scheduleTitle.textContent = `${monthNames[currentMonth]} ${selectedDay}, ${currentYear}`;
    
        try {
            const response = await fetch(`/get-schedule?date=${formattedDate}`);
            const schedule = await response.json();
    
            console.log("Fetched schedule:", schedule);  // Debugging: Check API response in console
    
            // Ensure schedule is an array and not empty
            if (!Array.isArray(schedule) || schedule.length === 0) {
                eventsList.innerHTML = "<p>No events scheduled.</p>";
                return;
            }
    
            // Map each event correctly
            eventsList.innerHTML = schedule.map(event => 
                `<div class="event">${event.task || "No Task"} <span>${event.time || "No Time"} ${event.status || ""}</span></div>`
            ).join("");
        } catch (error) {
            console.error("Error fetching schedule:", error);
            eventsList.innerHTML = "<p>Error loading schedule.</p>";
        }
    }
    

    // **Ensure the calendar is generated as soon as the page loads**
    updateCalendar();
    updateSchedule(currentDay);
});
