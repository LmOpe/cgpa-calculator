function app() {
    const headings = document.querySelectorAll('.result-heading');
    const dismissBtn = document.querySelector('.cancel span');
    const notice = document.querySelector('.notice');

    setTimeout(() => {
        notice.classList.toggle('inactive');
    }, 10000);

    notice.classList.toggle('inactive');

    headings.forEach(heading => {
        heading.addEventListener('click', () => {
            const session = heading.className.split(' ')[1];
            console.log(session)
            const current_rows = document.querySelectorAll(`[data-session=${'"' + session + '"'}]`);
            current_rows.forEach(row => {
                row.classList.toggle('inactive');
            })
            const th = heading.firstElementChild;
            const str = th.innerHTML;
            th.innerHTML = str.includes('Show') ? str.replace("Show", "Hide") : str.replace("Hide", "Show");
        })

    })


    dismissBtn.addEventListener('click', () => {
        notice.classList.toggle('inactive');
    })
}

app()