# Define tput color variables
green := $(shell tput setaf 2)
yellow := $(shell tput setaf 3)
red := $(shell tput setaf 1)
reset := $(shell tput sgr0)

PREFIX := BiliScript

# Define check step
check:
	@if [ ! -f "tool/runtime/python.exe" ]; then \
		echo -e "❌ ${red}Missing: ${green}tool/runtime/python.exe${reset}"; \
		exit 1; \
	fi
	@if [ ! -f "tool/ffmpeg/ffmpeg.exe" ]; then \
		echo -e "❌ ${red}Missing: ${green}tool/ffmpeg/ffmpeg.exe${reset}"; \
		exit 1; \
	fi
	@echo -e "✅ ${green}All files checked!${reset}"
	@if [ -d "runtime" ]; then \
		echo -e "💊 ${yellow}runtime exists. Run ${green}make clean${reset} first."; \
		exit 1; \
	fi

# Define the target to generate requirement.txt
requirement:
	uv export -q -o requirement.txt
	@echo -e "📄 ${green}Generated requirement.txt.${reset}"

# Define build target
build: check
	@echo -e "👻 ${yellow}Processing files...${reset}"
	# Copy the tool/runtime folder to the current directory
	@mkdir -p runtime
	@cp -r tool/runtime/* ./runtime/
	@echo -e "👻 ${green}Copied tool/runtime.${reset}"
	# Copy all files from tool/ffmpeg to the runtime directory
	@cp tool/ffmpeg/* ./runtime/
	@echo -e "👻 ${green}Copied tool/ffmpeg files.${reset}"
	# Execute dependency installation with retry mechanism
	@$(MAKE) pip

# addon
# @rsync -avq --delete tool/runtime/ ./runtime/

# Define the retry installation target for dependencies
pip:
	uv export -q -o tool/requirement.txt
	@max_retries=3; \
	count=0; \
	while [ $$count -le $$max_retries ]; do \
		if runtime/python.exe -m pip install --no-warn-script-location -r tool/requirement.txt; then \
			echo -e "✅ ${green}Dependencies installed!${reset}"; \
			rm -f tool/requirement.txt; \
			exit 0; \
		else \
			echo -e "👻 ${yellow}Install failed${reset}, retry $$count times..."; \
			count=$$((count + 1)); \
		fi; \
	done; \
	echo -e "❌ ${red}Install failed!${reset} Network may need a fix."; \
	exit 1

package:
	@{ git ls-files -co --exclude-standard; echo "runtime/"; } > tool/filelist.txt
	@if [ ! -s tool/filelist.txt ]; then \
		echo -e "🛑 ${red}Error: No files to compress!${reset}"; \
		rm -f tool/filelist.txt; \
		exit 1; \
	fi
	@7z a tool/$(PREFIX).$(shell date +"%Y-%m-%dT%H-%M-%S").7z @tool/filelist.txt
	rm -f tool/filelist.txt
	@echo -e "✅ ${green}Compression done!${reset}"

clean:
	@echo -e "👻 ${yellow}Removing the 'runtime' directory...${reset}"
	@rm -rf runtime
	@echo -e "✅ ${green}runtime directory cleaned!${reset}"

