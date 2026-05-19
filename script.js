document.addEventListener('DOMContentLoaded', () => {
    if ('scrollRestoration' in history) {
        history.scrollRestoration = 'manual';
    }
    window.scrollTo(0, 0);
    // Views
    const calculatorView = document.getElementById('calculator-view');
    const homeView = document.getElementById('home-view');
    const tournamentView = document.getElementById('tournament-view');
    
    // Calculator Elements
    const initialRatingInput = document.getElementById('initialRating');
    const matchesList = document.getElementById('matchesList');
    const addMatchBtn = document.getElementById('addMatchBtn');
    const resultToggle = document.getElementById('resultToggle');
    const toggleBtns = resultToggle.querySelectorAll('.toggle-btn');
    
    let selectedResult = 'win';

    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            toggleBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedResult = btn.dataset.value;
        });
    });

    const finalRatingResult = document.getElementById('finalRatingResult');
    const adjustedRatingContainer = document.getElementById('adjustedRatingContainer');
    const adjustedRatingResult = document.getElementById('adjustedRatingResult');
    const netChangeResult = document.getElementById('netChangeResult');
    
    const navCalcBtn = document.getElementById('navCalcBtn');
    const navTournamentsBtn = document.getElementById('navTournamentsBtn');

    // Tournament View Elements
    const tournamentGrid = document.getElementById('tournament-grid');
    const backBtn = document.getElementById('backBtn');
    const tournamentTitle = document.getElementById('tournamentTitle');
    
    const tableBody = document.getElementById('tableBody');
    const searchInput = document.getElementById('searchInput');
    const headers = document.querySelectorAll('th[data-sort]');
    
    // Modal Elements
    const playerModal = document.getElementById('playerModal');
    const modalPlayerName = document.getElementById('modalPlayerName');
    const statsSummary = document.getElementById('statsSummary');
    const matchList = document.getElementById('matchList');
    const closeModal = document.getElementById('closeModal');
    
    let ratingsData = [];
    let currentTournamentMatches = [];
    let currentSort = { column: 'final', direction: 'desc' };

    // --- Calculator Logic ---

    function calculatePoints(r_high, r_low, higherWon) {
        const diff = Math.abs(r_high - r_low);
        if (diff <= 12) return 8;
        else if (diff <= 37) return higherWon ? 7 : 10;
        else if (diff <= 62) return higherWon ? 6 : 13;
        else if (diff <= 87) return higherWon ? 5 : 16;
        else if (diff <= 112) return higherWon ? 4 : 20;
        else if (diff <= 137) return higherWon ? 3 : 25;
        else if (diff <= 162) return higherWon ? 2 : 30;
        else if (diff <= 187) return higherWon ? 2 : 35;
        else if (diff <= 212) return higherWon ? 1 : 40;
        else if (diff <= 237) return higherWon ? 1 : 45;
        else return higherWon ? 0 : 50;
    }

    function calcSpecialAdjustment(winsOpp, lossesOpp) {
        winsOpp.sort((a, b) => b - a);
        lossesOpp.sort((a, b) => a - b);
        
        if (lossesOpp.length === 0) {
            return winsOpp.slice(0, 2).reduce((a, b) => a + b, 0) / Math.min(winsOpp.length, 2);
        }
            
        const worstLoss = Math.min(...lossesOpp);
        const bestWin = Math.max(...winsOpp);
        
        if (worstLoss > bestWin) {
            return winsOpp.slice(0, 2).reduce((a, b) => a + b, 0) / Math.min(winsOpp.length, 2);
        }
            
        let cumSum = 0;
        let count = 0;
        
        for (let i = 0; i < Math.min(winsOpp.length, lossesOpp.length); i++) {
            const w = winsOpp[i];
            const l = lossesOpp[i];

            if (l > w) break;
                
            const testSum = cumSum + w + l;
            const testCount = count + 2;
            const testMean = testSum / testCount;
            
            if (count > 0) {
                if (w > testMean && l > testMean) {
                    cumSum += w;
                    count += 1;
                    break;
                } else if (w < testMean && l < testMean) {
                    cumSum += l;
                    count += 1;
                    break;
                }
            }
                    
            cumSum = testSum;
            count = testCount;
        }
        
        return count > 0 ? cumSum / count : 0;
    }

    function updateCalculator() {
        const initial = parseInt(initialRatingInput.value) || 0;
        const matchRows = document.querySelectorAll('.match-row');
        const matches = [];
        
        matchRows.forEach(row => {
            const result = row.dataset.result;
            const rating = parseInt(row.dataset.rating) || 0;
            matches.push({ result, rating });
        });

        if (initial === 0 && matches.length === 0) {
            finalRatingResult.textContent = '0';
            netChangeResult.textContent = '0';
            netChangeResult.className = 'result-value change-neutral';
            return;
        }

        let netPoints = 0;
        const winsPoints = [];
        const winsOpp = [];
        const lossesOpp = [];

        matches.forEach(m => {
            const isWin = m.result === 'win';
            const oppRating = m.rating;
            
            if (isWin) {
                const pts = calculatePoints(initial, oppRating, initial >= oppRating);
                netPoints += pts;
                winsPoints.push(pts);
                winsOpp.push(oppRating);
            } else {
                const pts = calculatePoints(oppRating, initial, oppRating >= initial);
                netPoints -= pts;
                lossesOpp.push(oppRating);
            }
        });

        let adjusted = null;
        if (initial > 0) {
            const c1 = netPoints >= 150;
            const c2 = winsPoints.filter(p => p === 50).length >= 3;
            let c3 = false;
            if (winsPoints.filter(p => p === 50).length >= 2) {
                const fiftyDiffs = matches
                    .filter(m => m.result === 'win' && calculatePoints(initial, m.rating, initial >= m.rating) === 50)
                    .map(m => m.rating - initial)
                    .sort((a, b) => b - a);
                if (fiftyDiffs.length >= 2 && (fiftyDiffs[0] + fiftyDiffs[1]) >= 700) {
                    c3 = true;
                }
            }

            if (c1 || c2 || c3) {
                adjusted = Math.round(calcSpecialAdjustment(winsOpp, lossesOpp));
            } else {
                const c4 = netPoints >= 60;
                const c5 = (netPoints >= 40) && (winsPoints.filter(p => p >= 20).length >= 2);
                if (c4 || c5) {
                    adjusted = initial + netPoints;
                }
            }
        } else {
            // Unrated logic
            if (winsOpp.length === 0 && lossesOpp.length === 0) {
                adjusted = 200;
            } else if (winsOpp.length === 0 && lossesOpp.length > 0) {
                adjusted = 200;
            } else if (lossesOpp.length === 0 && winsOpp.length > 0) {
                adjusted = Math.max(...winsOpp);
            } else {
                const worstLoss = Math.min(...lossesOpp);
                const bestWin = Math.max(...winsOpp);
                if (worstLoss >= bestWin) {
                    adjusted = bestWin;
                } else {
                    adjusted = Math.round(calcSpecialAdjustment(winsOpp, lossesOpp));
                }
                adjusted = Math.max(adjusted, 200);
            }
        }

        const baseline = adjusted !== null ? adjusted : initial;
        let finalNet = 0;

        matches.forEach(m => {
            const isWin = m.result === 'win';
            const oppRating = m.rating;
            
            if (isWin) {
                const pts = calculatePoints(baseline, oppRating, baseline >= oppRating);
                finalNet += pts;
            } else {
                const pts = calculatePoints(oppRating, baseline, oppRating >= baseline);
                const lossPts = (baseline < 100) ? Math.min(pts, 3) : pts;
                finalNet -= lossPts;
            }
        });

        const finalRating = baseline + finalNet;
        const change = finalRating - initial;

        if (adjusted !== null) {
            adjustedRatingContainer.classList.remove('hidden');
            adjustedRatingResult.textContent = adjusted;
        } else {
            adjustedRatingContainer.classList.add('hidden');
        }

        finalRatingResult.textContent = finalRating;
        netChangeResult.textContent = (change >= 0 ? '+' : '') + change;
        
        if (change > 0) netChangeResult.className = 'result-value change-positive';
        else if (change < 0) netChangeResult.className = 'result-value change-negative';
        else netChangeResult.className = 'result-value change-neutral';

        // Update individual match point indicators
        document.querySelectorAll('.match-row').forEach((row, idx) => {
            const m = matches[idx];
            if (!m) return;
            const isWin = m.result === 'win';
            
            // Initial Points (Phase 1)
            const ptsInitial = isWin 
                ? calculatePoints(initial, m.rating, initial >= m.rating)
                : calculatePoints(m.rating, initial, m.rating >= initial);
            
            const initialBadge = row.querySelector('.pts-initial');
            initialBadge.textContent = (isWin ? '+' : '-') + ptsInitial;
            initialBadge.className = 'pts-badge pts-initial ' + (isWin ? 'pts-win' : 'pts-loss');

            // Final Points (Phase 2)
            const ptsFinal = isWin 
                ? calculatePoints(baseline, m.rating, baseline >= m.rating)
                : calculatePoints(m.rating, baseline, m.rating >= baseline);
            
            const adjustedCol = row.querySelector('.pts-adjusted-col');
            const finalBadge = row.querySelector('.pts-final');
            
            if (adjusted !== null) {
                adjustedCol.classList.remove('hidden');
                finalBadge.textContent = (isWin ? '+' : '-') + ptsFinal;
                finalBadge.className = 'pts-badge pts-final ' + (isWin ? 'pts-win' : 'pts-loss');
            } else {
                adjustedCol.classList.add('hidden');
            }
        });
    }

    function addMatchRow(result = 'win', rating = 1500) {
        const row = document.createElement('div');
        row.className = 'match-row';
        row.dataset.result = result;
        row.dataset.rating = rating;

        const resultText = result.charAt(0).toUpperCase() + result.slice(1);
        const resultClass = result === 'win' ? 'change-positive' : 'change-negative';

        row.innerHTML = `
            <div class="match-info">
                <span class="match-result-text ${resultClass}">${resultText}</span>
                <span class="match-rating-text">vs ${rating}</span>
            </div>
            
            <div class="match-points">
                <div class="pts-column">
                    <span class="pts-label">Initial</span>
                    <div class="pts-badge pts-initial pts-neutral">0</div>
                </div>
                <div class="pts-column hidden pts-adjusted-col">
                    <span class="pts-label">Adjusted</span>
                    <div class="pts-badge pts-final pts-neutral">0</div>
                </div>
            </div>
            
            <button class="remove-match">×</button>
        `;
        
        row.querySelector('.remove-match').addEventListener('click', () => {
            row.remove();
            updateCalculator();
        });
        
        matchesList.appendChild(row);
        updateCalculator();
    }

    addMatchBtn.addEventListener('click', () => {
        const ratingInput = document.getElementById('newMatchRating');
        const rating = parseInt(ratingInput.value) || 0;
        
        if (rating > 0) {
            addMatchRow(selectedResult, rating);
            // Reset entry bar
            ratingInput.value = '1500';
            // Reset toggle
            toggleBtns.forEach(b => b.classList.remove('active'));
            toggleBtns[0].classList.add('active');
            selectedResult = 'win';
            // Focus back to input for rapid entry
            ratingInput.focus();
        }
    });

    document.getElementById('newMatchRating').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            addMatchBtn.click();
        }
    });
    
    initialRatingInput.addEventListener('input', updateCalculator);
    
    navTournamentsBtn.addEventListener('click', () => {
        calculatorView.classList.add('hidden');
        tournamentView.classList.add('hidden');
        homeView.classList.remove('hidden');
        
        navCalcBtn.classList.remove('active');
        navTournamentsBtn.classList.add('active');
        window.scrollTo(0, 0);
    });

    navCalcBtn.addEventListener('click', () => {
        homeView.classList.add('hidden');
        tournamentView.classList.add('hidden');
        calculatorView.classList.remove('hidden');
        
        navTournamentsBtn.classList.remove('active');
        navCalcBtn.classList.add('active');
        window.scrollTo(0, 0);
    });

    // --- Tournament View Logic ---

    // Load tournaments from offline data.js
    if (window.USATT_DATA) {
        const tournaments = window.USATT_TOURNAMENTS || Object.keys(window.USATT_DATA);
        renderTournamentGrid(tournaments);
    } else {
        tournamentGrid.innerHTML = `<p style="color:var(--accent-red)">Error: No offline data found. Wait for the automator to run or generate data.js.</p>`;
    }

    function renderTournamentGrid(tournaments) {
        tournamentGrid.innerHTML = '';
        tournaments.forEach(t => {
            const card = document.createElement('div');
            card.className = 'tournament-card';
            const bgUrl = `${encodeURIComponent(t)}/logo.jpg`;
            
            card.innerHTML = `
                <div class="card-bg" style="background-image: url('${bgUrl}');"></div>
                <div class="card-content">
                    <h3>${t}</h3>
                    <p>Click to view ratings</p>
                </div>
            `;
            card.addEventListener('click', () => openTournament(t));
            tournamentGrid.appendChild(card);
        });
    }

    function openTournament(name) {
        tournamentTitle.textContent = name;
        homeView.classList.add('hidden');
        tournamentView.classList.remove('hidden');
        window.scrollTo(0, 0);
        searchInput.value = ''; // Reset search
        
        tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center;">Loading data...</td></tr>`;
        
        if (window.USATT_DATA && window.USATT_DATA[name]) {
            const tournamentData = window.USATT_DATA[name];
            const players = tournamentData.players || tournamentData; // Backwards compatibility
            currentTournamentMatches = tournamentData.matches || [];
            
            // Map to internal format
            ratingsData = players.map(row => {
                const initial = parseInt(row['Initial Rating']) || 0;
                const change = parseInt(row['Rating Change']) || 0;
                
                return {
                    name: row['Player Name'],
                    initial: initial,
                    adjusted: row['Adjusted Rating'],
                    final: parseInt(row['Final Rating']) || 0,
                    change: change,
                    isUnrated: initial === 0
                };
            });
            
            // Initial sort by final rating descending
            currentSort = { column: 'final', direction: 'desc' };
            headers.forEach(h => {
                h.classList.remove('asc', 'desc');
                if(h.dataset.sort === 'final') h.classList.add('desc');
            });
            sortData('final', 'desc');
            renderTable(ratingsData);
        } else {
            console.error('Error loading data from offline DB');
            tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--accent-red)">Error loading data for this tournament.</td></tr>`;
        }
    }

    function openPlayerModal(player) {
        modalPlayerName.textContent = player.name;
        matchList.innerHTML = '';
        statsSummary.innerHTML = '';
        
        // Find player's matches
        const playerMatches = currentTournamentMatches.filter(m => 
            m.Winner === player.name || m.Loser === player.name
        );
        
        let wins = 0;
        let losses = 0;
        
        playerMatches.forEach(m => {
            const isWin = m.Winner === player.name;
            if (isWin) wins++; else losses++;
            
            const opponent = isWin ? m.Loser : m.Winner;
            const opponentRating = isWin ? m.LoserRating : m.WinnerRating;
            const resultClass = isWin ? 'win' : 'loss';
            const resultText = isWin ? 'Win' : 'Loss';
            
            const matchEl = document.createElement('div');
            matchEl.className = 'match-item';
            matchEl.innerHTML = `
                <div class="match-info">
                    <span class="match-opponent">${opponent} (${opponentRating})</span>
                    <span class="match-event">${m.Event}</span>
                </div>
                <div class="match-result ${resultClass}">${resultText}</div>
            `;
            matchList.appendChild(matchEl);
        });
        
        if (playerMatches.length === 0) {
            matchList.innerHTML = '<p style="text-align:center; opacity:0.5; padding: 1rem;">No match data available for this player.</p>';
        }
        
        statsSummary.innerHTML = `
            <div class="stat-card">
                <span class="stat-value" style="color:var(--accent-green)">${wins}</span>
                <span class="stat-label">Wins</span>
            </div>
            <div class="stat-card">
                <span class="stat-value" style="color:var(--accent-red)">${losses}</span>
                <span class="stat-label">Losses</span>
            </div>
        `;
        
        playerModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent scroll
    }

    closeModal.addEventListener('click', () => {
        playerModal.classList.add('hidden');
        document.body.style.overflow = '';
    });

    playerModal.addEventListener('click', (e) => {
        if (e.target === playerModal) closeModal.click();
    });

    backBtn.addEventListener('click', () => {
        tournamentView.classList.add('hidden');
        homeView.classList.remove('hidden');
        window.scrollTo(0, 0);
    });

    // Simple CSV parser
    function parseCSV(text) {
        const lines = text.split('\n');
        const result = [];
        if (lines.length === 0) return result;
        
        const headers = lines[0].split(',').map(h => h.trim());
        
        for (let i = 1; i < lines.length; i++) {
            if (!lines[i].trim()) continue;
            
            const obj = {};
            const currentline = lines[i].split(',');
            
            for (let j = 0; j < headers.length; j++) {
                obj[headers[j]] = currentline[j] ? currentline[j].trim() : '';
            }
            result.push(obj);
        }
        return result;
    }

    // Render table
    function renderTable(data) {
        tableBody.innerHTML = '';
        
        data.forEach((row, index) => {
            const tr = document.createElement('tr');
            tr.className = 'row-animate';
            tr.style.animationDelay = `${index * 0.02}s`;
            
            let changeClass = 'change-neutral';
            let changePrefix = '';
            
            if (row.change > 0) {
                changeClass = 'change-positive';
                changePrefix = '+';
            } else if (row.change < 0) {
                changeClass = 'change-negative';
            }
            
            let nameHtml = `<span class="player-name">${row.name}</span>`;
            if (row.isUnrated) {
                nameHtml += `<span class="badge">New</span>`;
            }

            tr.innerHTML = `
                <td>${nameHtml}</td>
                <td class="num-col">${row.initial}</td>
                <td class="num-col">${row.adjusted}</td>
                <td class="num-col" style="font-weight: 600; color: var(--accent-blue)">${row.final}</td>
                <td class="num-col ${changeClass}">${changePrefix}${row.change}</td>
            `;
            
            tr.addEventListener('click', () => openPlayerModal(row));
            tableBody.appendChild(tr);
        });
    }

    // Filter data
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filtered = ratingsData.filter(row => 
            row.name.toLowerCase().includes(searchTerm)
        );
        renderTable(filtered);
    });

    // Sort data
    function sortData(column, direction) {
        ratingsData.sort((a, b) => {
            let valA = a[column];
            let valB = b[column];
            
            if (column === 'initial' || column === 'final' || column === 'change') {
                return direction === 'asc' ? valA - valB : valB - valA;
            }
            
            if (column === 'adjusted') {
                if (valA === 'n/a') valA = -1; else valA = parseInt(valA) || 0;
                if (valB === 'n/a') valB = -1; else valB = parseInt(valB) || 0;
                return direction === 'asc' ? valA - valB : valB - valA;
            }
            
            return direction === 'asc' 
                ? valA.localeCompare(valB) 
                : valB.localeCompare(valA);
        });
    }

    // Header click handling
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.sort;
            
            let direction = 'desc';
            if (column === 'name') direction = 'asc';
            
            if (currentSort.column === column) {
                direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            }
            
            headers.forEach(h => h.classList.remove('asc', 'desc'));
            header.classList.add(direction);
            
            currentSort = { column, direction };
            
            sortData(column, direction);
            
            const searchTerm = searchInput.value.toLowerCase();
            const filtered = ratingsData.filter(row => 
                row.name.toLowerCase().includes(searchTerm)
            );
            
            renderTable(filtered);
        });
    });
});
