function app() {
    const headings = document.querySelectorAll('.result-heading');

    headings.forEach(heading => {
        heading.addEventListener('click', () => {
            const session = heading.className.split(' ')[1];
            console.log(session);
            current_rows = document.querySelectorAll(`[data-session=${'"' + session + '"'}]`);
            current_rows.forEach(row => {
                row.classList.toggle('inactive');
            })
        })

    })
}

app()