document.addEventListener("DOMContentLoaded", function () {
    // Fetch documents from the server
    fetchDocuments();

    function fetchDocuments() {
        fetch("/dashboard/documents/")
        .then(response => response.json())
        .then(data => {
            console.log("Fetched Data:", data);

            if (!data.documents || data.documents.length === 0) {
                handleNoDocuments();
                return;
            }

            populateFeaturedDocuments(data.documents.slice(0, 3));
            populateDocumentsTable(data.documents);
        })
        .catch(error => {
            console.error("Error fetching documents:", error);
            handleFetchError();
        });
    }

    function handleNoDocuments() {
        document.getElementById("featured-document-list").innerHTML = 
            '<div class="no-documents">No documents available at this time</div>';
        document.getElementById("table-body").innerHTML = 
            '<tr><td colspan="3" class="no-documents">No documents available at this time</td></tr>';
    }

    function handleFetchError() {
        document.getElementById("featured-document-list").innerHTML = 
            '<div class="no-documents">Error loading documents. Please try again later.</div>';
        document.getElementById("table-body").innerHTML = 
            '<tr><td colspan="3" class="no-documents">Error loading documents. Please try again later.</td></tr>';
    }

    function populateFeaturedDocuments(documents) {
        const featuredDocumentList = document.getElementById("featured-document-list");
        featuredDocumentList.innerHTML = "";

        documents.forEach(doc => {
            const card = document.createElement("div");
            card.classList.add("card");

            const fileName = document.createElement("h3");
            fileName.textContent = doc.file;
            fileName.setAttribute("title", doc.file);
            card.appendChild(fileName);

            const details = document.createElement("div");
            details.classList.add("details");
            for (const [key, value] of Object.entries(doc.details)) {
                const p = document.createElement("p");
                p.innerHTML = `<strong>${key}:</strong> ${value || "N/A"}`;
                details.appendChild(p);
            }

            card.appendChild(details);
            featuredDocumentList.appendChild(card);
        });
    }

    function populateDocumentsTable(documents) {
        const tableBody = document.getElementById("table-body");
        tableBody.innerHTML = "";

        documents.forEach(doc => {
            const row = document.createElement("tr");

            const fileNameCell = document.createElement("td");
            fileNameCell.textContent = doc.file;
            fileNameCell.setAttribute("title", doc.file);
            row.appendChild(fileNameCell);

            const detailsCell = document.createElement("td");
            const detailsList = document.createElement("ul");
            detailsList.classList.add("details-list");

            for (const [key, value] of Object.entries(doc.details)) {
                const listItem = document.createElement("li");
                listItem.innerHTML = `<strong>${key}:</strong> ${value || "N/A"}`;
                detailsList.appendChild(listItem);
            }

            detailsCell.appendChild(detailsList);
            row.appendChild(detailsCell);

            const actionCell = document.createElement("td");
            const viewReportBtn = document.createElement("a");
            viewReportBtn.href = `/showcase_report/?document_name=${encodeURIComponent(doc.file)}`;
            viewReportBtn.classList.add("view-report-btn");
            viewReportBtn.textContent = "View Report";
            actionCell.appendChild(viewReportBtn);
            row.appendChild(actionCell);

            tableBody.appendChild(row);
        });
    }
});
